# Copyright (c) 2026 Push
"""Digest, critical-alert, weekly and short chat messages.

Ported from geonews reports/email_report.py, critical_alert.py,
weekly_report.py, telegram_report.py, whatsapp_report.py and the subject /
skip rules in apps_script/Code.gs. Same sections, order, wording, colours,
limits and thresholds. Pure: take already-selected rows, return strings.
All text is HTML-escaped; links are https-only (checked in model.normalise).
"""
import html
from collections import defaultdict
from datetime import timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from . import _safe, model

CATEGORY_LABELS = {
    "GEOPOLITICS": "\U0001F30D Geopolitics",
    "CONFERENCE": "\U0001F5D3\uFE0F Conferences & Meetings",
    "TRADE": "\U0001F4E6 Trade Activity",
    "SANCTIONS": "\U0001F6AB Sanctions & Circulars",
    "RISK": "\u26A0\uFE0F Risk Signals",
    "RESEARCH": "\U0001F4C4 Research Papers & Documents",
    "GENERAL": "\U0001F4F0 Other",
}
WEEKLY_LABELS = {
    "GEOPOLITICS": "Geopolitics", "CONFERENCE": "Conferences & Meetings",
    "TRADE": "Trade Activity", "SANCTIONS": "Sanctions & Circulars",
    "RISK": "Risk Signals", "RESEARCH": "Research Papers & Documents", "GENERAL": "Other",
}
RISK_COLORS = {"CRITICAL": "#c53030", "HIGH": "#dd6b20", "MODERATE": "#d69e2e", "LOW": "#718096"}
CRED_COLORS = {"HIGH": "#2f855a", "MEDIUM": "#b7791f", "LOW": "#a0aec0"}


def E(text):
    return html.escape(str(text))


_IST = timezone(timedelta(hours=5, minutes=30), "IST")


def _tz(settings):
    """Zone database missing (slim image) or bad name -> fixed +05:30 (IST)."""
    try:
        return ZoneInfo(settings.display_tz)
    except (ZoneInfoNotFoundError, ValueError, OSError):
        return _IST


def _local(now, settings):
    return now.astimezone(_tz(settings))


def _zone(now, settings):
    return _local(now, settings).strftime("%Z") or settings.display_tz


def group_articles(articles, min_score):
    grouped = defaultdict(list)
    for a in articles:
        if a["score"] < min_score:
            continue
        grouped[a["category"] or "GENERAL"].append(a)
    return grouped


def _section_html(category, items):
    label = CATEGORY_LABELS.get(category, category.title())
    rows = [f"<h2 style='margin:28px 0 12px;font-size:19px;color:#1a365d;"
            f"border-bottom:2px solid #e2e8f0;padding-bottom:6px'>{E(label)} "
            f"<span style='font-size:13px;color:#718096;font-weight:normal'>({len(items)})</span></h2>"]
    for a in items:
        color = RISK_COLORS.get(a["risk_level"], "#718096")
        cred = a["credibility"]
        cred_color = CRED_COLORS.get(cred, "#a0aec0")
        corr = a["corroboration"]
        country = f" &middot; {E(a['country'])}" if a["country"] else ""
        confirmed = f" &middot; confirmed by {corr} sources" if corr > 1 else ""
        rows.append(f"""
        <div style="margin-bottom:18px;padding:14px 16px;border-left:4px solid {color};background:#f7fafc;border-radius:4px">
            <div style="font-size:11px;color:#718096;font-weight:600;text-transform:uppercase;margin-bottom:4px">
                {E(a['source'])} &middot;
                <span style="color:{cred_color}">{E(cred)} credibility</span> &middot;
                <span style="color:{color}">{E(a['risk_level'])}</span> &middot; score {a['score']}/100
                {country}
                {confirmed}
            </div>
            <h3 style="margin:0 0 6px;font-size:15px;line-height:1.4">
                <a href="{E(a['url'])}" style="color:#1a365d;text-decoration:none">{E(a['title'])}</a>
            </h3>
            <p style="margin:0;font-size:13px;color:#2d3748;line-height:1.5">{E(a['summary'][:600])}</p>
        </div>""")
    return "".join(rows)


class Digest:
    """Result of build_digest(). `refs` are the handles to mark as sent AFTER a
    confirmed send (geonews: article_ids). Never printed in any output."""
    __slots__ = ("html", "subject", "critical_count", "refs", "shown", "selected")

    def __init__(self, html_, subject, critical_count, refs, shown, selected):
        self.html, self.subject, self.critical_count = html_, subject, critical_count
        self.refs, self.shown, self.selected = refs, shown, selected

    def to_digest_data(self):
        """Same JSON shape as geonews GET /digest-data (html, critical_count, article_ids)."""
        return {"html": self.html, "critical_count": self.critical_count, "article_ids": list(self.refs)}


def digest_subject(now, critical_count, settings=model.Settings()):
    """Apps Script wording: 'Geo Intel Brief - dd Mon yyyy HH:mm [ - N CRITICAL]'."""
    stamp = _local(now, settings).strftime("%d %b %Y %H:%M") + " " + _zone(now, settings)
    base = "\U0001F30D Geo Intel Brief \u2014 " + stamp
    return base + (f"  \u26A0\uFE0F {critical_count} CRITICAL" if critical_count > 0 else "")


def should_send_digest(digest):
    """Apps Script rule: skip when nothing new AND nothing critical."""
    return bool(digest.refs) or digest.critical_count > 0


def build_digest(articles, events, now, settings=model.Settings()):
    """articles: normalised rows (model.normalise_all); events: raw event rows.
    Selection and layout follow geonews email_report.build_digest()."""
    selected = model.unemailed_articles(articles, settings.digest_limit, settings.min_score)
    evs = model.upcoming_events(events, now, settings.upcoming_days)
    grouped = group_articles(selected, settings.min_score)
    total_relevant = sum(len(v) for v in grouped.values())
    critical_count = sum(1 for a in selected if a["risk_level"] == "CRITICAL")
    today = _local(now, settings).strftime("%d %B %Y") + " (" + _zone(now, settings) + ")"
    dash = ""
    if settings.dashboard_url:
        u = _safe.clean_dashboard_url(settings.dashboard_url)
        if u:
            dash = f' &middot; <a href="{E(u)}" style="color:#2b6cb0">\U0001F4CA View full dashboard</a>'
    body = [f"""<html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Segoe UI,Arial,sans-serif">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:20px 0"><tr><td align="center">
    <table width="700" style="background:#ffffff;border-radius:10px;overflow:hidden">
    <tr><td style="background:linear-gradient(135deg,#1a365d,#2b6cb0);padding:26px 30px;color:white">
        <h1 style="margin:0;font-size:22px">\U0001F30D Global Geopolitical Intelligence \u2014 Daily Brief</h1>
        <p style="margin:8px 0 0;font-size:13px;opacity:0.9">{E(today)}</p>
    </td></tr>
    <tr><td style="padding:18px 30px;background:#edf2f7;font-size:13px;color:#2d3748">
        <b>{total_relevant}</b> relevant items &middot;
        <b style="color:#c53030">{critical_count}</b> critical &middot;
        <b>{len(evs)}</b> upcoming events in next {settings.upcoming_days} days
        {dash}
    </td></tr>
    <tr><td style="padding:10px 30px 25px">"""]
    if evs:
        body.append("<h2 style='margin:20px 0 12px;font-size:19px;color:#1a365d;"
                    "border-bottom:2px solid #e2e8f0;padding-bottom:6px'>\U0001F5D3\uFE0F Upcoming Events</h2>")
        for e in evs:
            link = f'<a href="{E(e["source_url"])}" style="font-size:12px;color:#2b6cb0">Source \u2192</a>' if e["source_url"] else ""
            body.append(f"""<div style="margin-bottom:12px;padding:10px 14px;background:#f7fafc;border-radius:4px">
                <b>{E(e['name'])}</b><br>
                <span style="font-size:12px;color:#718096">{E(e['event_date'].isoformat())} &middot;
                {E(e['category'])} &middot; {E(e['confidence'])}</span>
                <p style="margin:6px 0 0;font-size:13px">{E(e['description'])}</p>
                {link}
            </div>""")
    if total_relevant == 0:
        body.append("<p style='color:#718096'>No items scored above the relevance threshold this cycle.</p>")
    else:
        order = list(settings.active_categories) + [c for c in grouped if c not in settings.active_categories]
        for category in order:
            if grouped.get(category):
                items = sorted(grouped[category], key=lambda a: a["score"], reverse=True)
                body.append(_section_html(category, items))
    body.append("""</td></tr>
    <tr><td style="background:#f7fafc;padding:16px 30px;text-align:center;font-size:12px;color:#718096">
        Auto-generated briefing. Verify important information with the original source.
    </td></tr>
    </table></td></tr></table></body></html>""")
    refs = [a["ref"] for a in selected if a["ref"]]
    return Digest("".join(body), digest_subject(now, critical_count, settings), critical_count, refs,
                  total_relevant, len(selected))


# ---------------- instant critical alert ----------------

def alert_subject(n):
    return f"\U0001F6A8 CRITICAL Geo Intel Alert \u2014 {n} item(s)"


def build_alert(items, now, settings=model.Settings()):
    """items: model.critical_since() result. Returns (subject, html)."""
    stamp = _local(now, settings).strftime("%d %b %Y | %H:%M") + " " + _zone(now, settings)
    rows = [f"""<html><body style="font-family:Segoe UI,Arial,sans-serif;background:#fff5f5;padding:20px">
    <div style="max-width:640px;margin:auto;background:white;border:2px solid #c53030;border-radius:8px;overflow:hidden">
    <div style="background:#c53030;color:white;padding:18px 24px">
        <h1 style="margin:0;font-size:19px">\U0001F6A8 Critical Geo Intel Alert</h1>
        <p style="margin:6px 0 0;font-size:12px;opacity:0.9">{E(stamp)}</p>
    </div>
    <div style="padding:20px 24px">"""]
    for a in items:
        country = f" &middot; {E(a['country'])}" if a["country"] else ""
        rows.append(f"""
        <div style="margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #fed7d7">
            <div style="font-size:11px;color:#718096;font-weight:600;text-transform:uppercase">
                {E(a['source'])} &middot; score {a['score']}/100
                {country}
            </div>
            <h3 style="margin:4px 0 6px;font-size:15px">
                <a href="{E(a['url'])}" style="color:#c53030;text-decoration:none">{E(a['title'])}</a>
            </h3>
            <p style="margin:0;font-size:13px;color:#2d3748">{E(a['summary'][:400])}</p>
        </div>""")
    rows.append("</div></div></body></html>")
    return alert_subject(len(items)), "".join(rows)


# ---------------- weekly summary ----------------

def build_weekly(articles, now, settings=model.Settings()):
    """Returns (subject, html). Same sections as geonews weekly_report.build_html."""
    days = settings.weekly_days
    top = model.weekly_top_articles(articles, now, days, settings.weekly_limit)
    cats = model.category_counts(articles, now, days)
    countries = model.top_countries(articles, now, days, settings.weekly_countries)
    asof = _local(now, settings).strftime("%d %b %Y") + " " + _zone(now, settings)
    body = [f"""<html><body style="margin:0;padding:0;background:#f4f6f8;font-family:Segoe UI,Arial,sans-serif">
    <table width="100%" cellpadding="0" cellspacing="0" style="padding:20px 0"><tr><td align="center">
    <table width="680" style="background:white;border-radius:10px;overflow:hidden">
    <tr><td style="background:linear-gradient(135deg,#2d3748,#4a5568);color:white;padding:24px 28px">
        <h1 style="margin:0;font-size:20px">\U0001F4CA Weekly Geo Intel Summary</h1>
        <p style="margin:6px 0 0;font-size:12px;opacity:0.9">Last {days} days, as of {E(asof)}</p>
    </td></tr>
    <tr><td style="padding:22px 28px">"""]
    if cats:
        body.append("<h2 style='font-size:16px;color:#1a365d'>Volume by category</h2><table style='width:100%;font-size:13px;margin-bottom:20px'>")
        for c, n in cats:
            label = WEEKLY_LABELS.get(c, c or "Other")
            body.append(f"<tr><td style='padding:3px 0'>{E(label)}</td><td style='text-align:right;color:#2b6cb0;font-weight:600'>{n}</td></tr>")
        body.append("</table>")
    if countries:
        body.append("<h2 style='font-size:16px;color:#1a365d'>Most-mentioned countries</h2><p style='font-size:13px;color:#2d3748;margin-bottom:20px'>")
        body.append(" &nbsp;&middot;&nbsp; ".join(f"{E(c)} ({n})" for c, n in countries))
        body.append("</p>")
    body.append("<h2 style='font-size:16px;color:#1a365d'>Top stories this week</h2>")
    if not top:
        body.append("<p style='color:#718096'>No items in the supplied data for this period. "
                    "This does not mean nothing happened.</p>")
    for a in top:
        body.append(f"""
        <div style="margin-bottom:14px;padding-bottom:12px;border-bottom:1px solid #e2e8f0">
            <div style="font-size:11px;color:#718096;text-transform:uppercase">{E(a['source'])} &middot; {E(a['risk_level'])} &middot; {a['score']}/100</div>
            <a href="{E(a['url'])}" style="font-size:14px;color:#1a365d;text-decoration:none;font-weight:600">{E(a['title'])}</a>
        </div>""")
    body.append("""</td></tr>
    <tr><td style="background:#f7fafc;padding:14px 28px;text-align:center;font-size:12px;color:#718096">
        Auto-generated weekly rollup.
    </td></tr></table></td></tr></table></body></html>""")
    return "\U0001F4CA Geo Intel Weekly Summary \u2014 " + asof, "".join(body)


# ---------------- Telegram / WhatsApp short digests ----------------

def _md(text):
    """Escape Telegram legacy-Markdown specials so a title cannot break the send."""
    for ch in ("\\", "_", "*", "`", "["):
        text = text.replace(ch, "\\" + ch)
    return text


def _md_url(url):
    """URL as plain text inside legacy Markdown: escape specials, ')' as %29."""
    return _md(url).replace(")", "%29")


def _cut(msg, limit, tail="\n\n...(truncated)"):
    """Truncate at a line boundary (never inside an escape or a link)."""
    if len(msg) <= limit:
        return msg
    head = msg[:limit]
    nl = head.rfind("\n")
    return (head[:nl] if nl > 0 else "") + tail


def _chat_lines(articles, events, now, settings, limit, with_url, md):
    # geonews: recent_articles() = best by score (limit 60), then score >= 4, then [:limit]
    arts = [a for a in sorted(articles, key=model.by_score_then_published)[:60]
            if a["score"] >= settings.chat_min_score][:limit]
    evs = model.upcoming_events(events, now, settings.upcoming_days)[:3]
    esc = _md if md else (lambda t: t)
    lines = ["*Global Geopolitical Intelligence*", ""]
    if with_url and settings.dashboard_url:
        u = _safe.clean_dashboard_url(settings.dashboard_url)
        if u:
            lines += [f"\U0001F4CA [View full dashboard]({_md_url(u) if md else u})", ""]
    if evs:
        lines.append("*Upcoming:*")
        for e in evs:
            lines.append(f"- {esc(e['name'][:70])} ({e['event_date'].isoformat()})")
        lines.append("")
    lines.append("*Top developments:*")
    for i, a in enumerate(arts, 1):
        lines.append(f"{i}. [{a['risk_level']}] {esc(a['title'][:80])}")
        lines.append(f"   _{esc(a['source'])}_" + (f" - {_md_url(a['url']) if md else a['url']}" if with_url else ""))
    if not arts:
        lines.append("No high-relevance items this cycle.")
    return lines


def build_telegram_message(articles, events, now, settings=model.Settings()):
    msg = "\n".join(_chat_lines(articles, events, now, settings, settings.chat_telegram_limit, True, True))
    return _cut(msg, 4000)


def build_whatsapp_message(articles, events, now, settings=model.Settings()):
    msg = "\n".join(_chat_lines(articles, events, now, settings, settings.chat_whatsapp_limit, False, False))
    return _cut(msg, 3900)
