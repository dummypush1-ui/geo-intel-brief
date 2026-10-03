"""Pure copied BRICS processing rules for supplied offline candidates.

Rules/functions copied from preserved classifier.py and dedupe.py. Only the
implicit configured threshold fallback is removed: caller must pass threshold.
No config/secret/env/dotenv access, file reads, network or persistence.
This is a processing snapshot, not proof of current production configuration.
"""
from difflib import SequenceMatcher

KEYWORDS = {
    "GEOPOLITICS": ["summit", "diplomat", "bilateral", "foreign minister", "president", "prime minister"],
    "TRADE": ["trade", "export", "import", "tariff", "supply chain", "currency"],
    "SANCTIONS": ["sanction", "embargo", "blacklist", "restricted"],
    "RISK": ["attack", "explosion", "unrest", "coup", "conflict", "ceasefire"],
    "CONFERENCE": ["conference", "meeting", "forum", "declaration", "summit"],
}

def classify(article):
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    for cat, words in KEYWORDS.items():
        if any(w in text for w in words):
            return cat
    return "GENERAL"

STRONG_SIGNALS = [
    "brics", "new delhi declaration", "bharat mandapam", "18th brics",
    "brics summit", "brics nations", "brics countries", "brics leaders",
]

LEADER_NAMES = [
    "modi", "putin", "xi jinping", "ramaphosa", "lula", "abiy ahmed",
    "prabowo", "pezeshkian", "el-sisi", "al nahyan", "faisal al saud",
]

DIPLOMATIC_TERMS = [
    "summit", "bilateral meeting", "bilateral talks", "joint statement",
    "multilateral", "state visit", "delegation", "foreign minister meeting",
    "trade agreement", "trade deal", "de-dollarization", "currency pact",
    "diplomatic", "sanctions", "new delhi", "declaration",
]

def is_brics_relevant(article):
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    if any(kw in text for kw in STRONG_SIGNALS):
        return True
    has_leader = any(kw in text for kw in LEADER_NAMES)
    has_diplomatic_term = any(kw in text for kw in DIPLOMATIC_TERMS)
    return has_leader and has_diplomatic_term

def filter_brics(articles):
    return [a for a in articles if is_brics_relevant(a)]

def _similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def dedupe(articles, threshold):
    kept = []
    for art in articles:
        dup = False
        for k in kept:
            if _similar(art["title"], k["title"]) >= threshold:
                k.setdefault("corroborated_by", [k["source"]])
                if art["source"] not in k["corroborated_by"]:
                    k["corroborated_by"].append(art["source"])
                dup = True
                break
        if not dup:
            kept.append(art)
    return kept
