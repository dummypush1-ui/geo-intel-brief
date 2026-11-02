"""Two-way link between news and HS codes.

news -> codes : tag_text(title + summary)  -> [{code, label, score, via, terms}]
code -> news  : news_for_code("8542")      -> recent BRICS + Geo articles tagged with that heading

Matching is deliberately conservative (precision over recall) and explainable:
  1. curated phrase aliases   (hsn/data/news_aliases.json, editable)  -> strong
  2. lexicon overlap          (WCO HS heading text, IDF-weighted)     -> needs >=2 rare words
Every tag says WHY it matched (`terms`), so a wrong tag is easy to spot and fix.
"""
import json
import logging
import math
import re
import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

log = logging.getLogger("crosslink")
_DATA = Path(__file__).resolve().parent.parent / "hsn" / "data"

_TOKEN = re.compile(r"[a-z][a-z\-]{3,}")
_STOP = set("""
other others thereof their there these those which where while with without from into onto over under between
including included excluding except whether whose such than then them were been being have having does done made make
parts part articles article products product goods kind kinds type types used uses using like similar nesoi
containing contain consisting consist prepared preparations preparation whether form forms
""".split())

_lock = threading.Lock()
_lex = None


def _stem(w):
    for suf in ("ies", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 4:
            return w[: -len(suf)] + ("y" if suf == "ies" else "")
    return w


def _tokens(text):
    return {_stem(t) for t in _TOKEN.findall(text.lower()) if t not in _STOP}


class _Lexicon:
    def __init__(self):
        raw = json.loads((_DATA / "lexicon.json").read_text())
        self.label = {c: d for c, d in raw["headings"]}
        docs = defaultdict(set)                      # heading -> tokens
        for c, d in raw["headings"]:
            docs[c] |= _tokens(d)
        for c6, d in raw["hs6"]:
            docs[c6[:4]] |= _tokens(d)
        df = defaultdict(int)
        for toks in docs.values():
            for t in toks:
                df[t] += 1
        n = max(len(docs), 1)
        self.idf = {t: math.log(n / v) for t, v in df.items()}
        self.index = defaultdict(set)                # token -> headings
        for c, toks in docs.items():
            for t in toks:
                if self.idf[t] >= 3.2:               # only distinctive words are indexed
                    self.index[t].add(c)
        raw_alias = json.loads((_DATA / "news_aliases.json").read_text())
        self.alias = {k: v for k, v in raw_alias.items() if not k.startswith("_")}
        pats = sorted(self.alias, key=len, reverse=True)
        self.alias_re = re.compile(r"(?<![a-z0-9])(" + "|".join(re.escape(p) for p in pats) + r")(?![a-z0-9])")
        self.chapter_of = {c: c[:2] for c in self.label}


def lexicon():
    global _lex
    if _lex is None:
        with _lock:
            if _lex is None:
                _lex = _Lexicon()
    return _lex


def heading_label(code4):
    d = lexicon().label.get(code4, "")
    d = re.sub(r"\s+", " ", d).strip()
    return (d[:90] + "…") if len(d) > 90 else d


def tag_text(text, max_codes=4):
    """Return HS-heading tags for a piece of news text."""
    if not text:
        return []
    L = lexicon()
    low = text.lower()
    scores, why, via = defaultdict(float), defaultdict(list), {}
    # 1) curated aliases
    seen = defaultdict(int)
    for m in L.alias_re.finditer(low):
        seen[m.group(1)] += 1
    for phrase, n in seen.items():
        for code in L.alias[phrase]:
            scores[code] += 3.0 + 0.5 * min(n - 1, 3)
            if phrase not in why[code]:
                why[code].append(phrase)
            via[code] = "alias"
    # 2) lexicon overlap: need >=2 distinct distinctive words from the same heading
    toks = _tokens(low)
    hit = defaultdict(set)
    for t in toks:
        for code in L.index.get(t, ()):
            hit[code].add(t)
    for code, ts in hit.items():
        if len(ts) >= 2:
            s = sum(L.idf[t] for t in ts) / 4.0
            if code not in scores:
                via[code] = "lexicon"
            scores[code] += s
            for t in sorted(ts):
                if t not in why[code]:
                    why[code].append(t)
    ranked = sorted(scores.items(), key=lambda kv: -kv[1])[:max_codes]
    return [dict(code=c, label=heading_label(c), score=round(s, 1), via=via[c], terms=why[c][:5]) for c, s in ranked
            if via[c] == "alias" or s >= 3.0]


# ---------------------------------------------------------------- article sources
_cache = {"t": 0.0, "rows": []}
_cache_lock = threading.Lock()
TTL = 120


def _norm_date(a):
    return (a.get("published") or a.get("collected_at") or "")[:10]


def _recent_articles(limit=400):
    """BRICS + Geo articles, normalised. Each source fails independently."""
    rows = []
    try:
        from brics.database import get_store
        from brics.processing.classifier import filter_brics
        for a in filter_brics(get_store().recent(limit)):
            rows.append(dict(app="brics", title=a.get("title", ""), url=a.get("url", ""), source=a.get("source", ""),
                             date=_norm_date(a), text=a.get("title", ""), country=a.get("country", "")))
    except Exception as e:  # noqa: BLE001
        log.info("crosslink: brics source unavailable (%s)", type(e).__name__)
    try:
        from geonews.database import recent_articles
        for a in recent_articles(limit=limit, sort_by="newest") or []:
            rows.append(dict(app="geo", title=a.get("title", ""), url=a.get("url", ""), source=a.get("source", ""),
                             date=_norm_date(a), text=f"{a.get('title', '')}. {a.get('summary') or ''}",
                             country=a.get("country", "")))
    except Exception as e:  # noqa: BLE001
        log.info("crosslink: geo source unavailable (%s)", type(e).__name__)
    return rows


def _articles():
    with _cache_lock:
        if time.time() - _cache["t"] < TTL and _cache["rows"]:
            return _cache["rows"]
    rows = _recent_articles()
    seen, out = set(), []
    for r in rows:                      # de-duplicate on URL (the same story is often in both apps)
        k = r["url"] or r["title"]
        if k in seen or not r["title"] or not str(r["url"]).lower().startswith(("http://", "https://")):
            continue
        seen.add(k)
        r["tags"] = tag_text(r["text"])
        out.append(r)
    with _cache_lock:
        _cache.update(t=time.time(), rows=out)
    return out


def news_for_code(code, days=30, limit=12):
    """Recent news whose text maps to this HS code's 4-digit heading (or chapter, for 2 digits)."""
    digits = re.sub(r"\D", "", code or "")
    if len(digits) < 2:
        return dict(ok=False, error="code must have at least 2 digits")
    L = lexicon()
    head = digits[:4]
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    hits = []
    for r in _articles():
        if r["date"] and r["date"] < cutoff:
            continue
        for t in r["tags"]:
            if (len(digits) == 2 and t["code"][:2] == digits) or (len(digits) >= 4 and t["code"] == head):
                hits.append((t["score"], r["date"], r, t))
                break
    hits.sort(key=lambda x: (x[1], x[0]), reverse=True)          # newest first, score as tie-break
    items = [dict(title=r["title"], url=r["url"], source=r["source"], date=r["date"], app=r["app"],
                  matched=t["terms"], via=t["via"], heading=t["code"]) for _, _, r, t in hits[:limit]]
    return dict(ok=True, code=digits, heading=head if len(digits) >= 4 else None,
                heading_label=heading_label(head) if len(digits) >= 4 and head in L.label else None,
                days=days, count=len(hits), items=items)
