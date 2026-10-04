# Copyright (c) 2026 Push
"""Delivery code ported from geonews (SMTP mail, Telegram Bot API, CallMeBot
WhatsApp) and the send-then-mark-sent flow, DEFAULT OFF.

Nothing here runs at import. Nothing sends unless the caller passes
enabled=True explicitly AND supplies credentials as arguments (no env-var
or file reads). With enabled=False (the default) every function builds what
it would send and returns it as a dry run: no sockets, no marking.
Secrets live only in the sender closure; they never appear in repr, errors or
return values.
"""
import http.client
import re
import smtplib
import ssl
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from . import model, render

_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_TOKEN_RE = re.compile(r"\A[0-9]{5,15}:[A-Za-z0-9_-]{20,80}\Z")
_CHAT_RE = re.compile(r"\A(-?[0-9]{1,20}|@[A-Za-z0-9_]{5,32})\Z")
_HEADER_BAD = re.compile(r"[\r\n\x00]")


class DeliveryDisabled(RuntimeError):
    pass


class DeliveryError(RuntimeError):
    """Message never contains URLs, tokens or passwords."""


def _need_enabled(enabled):
    if enabled is not True:
        raise DeliveryDisabled("delivery is off (pass enabled=True explicitly to turn it on)")


def _check_header(value, name):
    if not isinstance(value, str) or not value or _HEADER_BAD.search(value):
        raise ValueError("%s is not a safe header value" % name)
    return value


def _recipients(to):
    items = [x.strip() for x in to.split(",")] if isinstance(to, str) else list(to or [])
    if not items or len(items) > 20 or not all(isinstance(x, str) and _EMAIL_RE.match(x) for x in items):
        raise ValueError("recipients must be 1-20 valid email addresses")
    return items


# ------------------------------------------------------------ transports

def smtp_sender(*, enabled=False, host, port=465, user, password, mail_from, mail_to, timeout=30):
    """-> sender(subject, html) using SMTP over SSL (geonews email_report.send)."""
    _need_enabled(enabled)
    to = _recipients(mail_to)
    frm = _check_header(mail_from, "mail_from")
    if not _EMAIL_RE.match(frm):
        raise ValueError("mail_from is not a valid address")

    def send(subject, html_body):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = _check_header(subject, "subject")
        msg["From"] = frm
        msg["To"] = ", ".join(to)
        msg.attach(MIMEText(html_body, "html", "utf-8"))
        try:
            with smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=timeout) as server:
                server.login(user, password)
                server.sendmail(frm, to, msg.as_string())
        except (smtplib.SMTPException, OSError) as exc:
            raise DeliveryError("SMTP send failed (%s)" % type(exc).__name__) from None
    return send


def telegram_sender(*, enabled=False, bot_token, chat_id, timeout=20):
    """-> sender(text) via the Telegram Bot API (geonews telegram_report.send)."""
    _need_enabled(enabled)
    if not isinstance(bot_token, str) or not _TOKEN_RE.match(bot_token):
        raise ValueError("bot_token has an invalid format")
    if not isinstance(chat_id, (str, int)) or not _CHAT_RE.match(str(chat_id)):
        raise ValueError("chat_id has an invalid format")

    def send(text):
        data = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "parse_mode": "Markdown",
                                       "disable_web_page_preview": "true"}).encode()
        req = urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % bot_token, data=data)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if r.status != 200:
                    raise DeliveryError("Telegram HTTP %s" % r.status)
        except urllib.error.HTTPError as exc:
            raise DeliveryError("Telegram HTTP %s" % exc.code) from None
        except (urllib.error.URLError, OSError) as exc:
            raise DeliveryError("Telegram send failed (%s)" % type(exc).__name__) from None
        except (ValueError, http.client.HTTPException):
            raise DeliveryError("invalid request") from None
    return send


def whatsapp_sender(*, enabled=False, phone, apikey, timeout=20):
    """-> sender(text) via CallMeBot (geonews whatsapp_report.send)."""
    _need_enabled(enabled)
    if not phone or not apikey:
        raise ValueError("phone and apikey are required")

    def send(text):
        q = urllib.parse.urlencode({"phone": phone, "text": text, "apikey": apikey})
        try:
            with urllib.request.urlopen("https://api.callmebot.com/whatsapp.php?" + q, timeout=timeout) as r:
                if r.status != 200:
                    raise DeliveryError("CallMeBot HTTP %s" % r.status)
        except urllib.error.HTTPError as exc:
            raise DeliveryError("CallMeBot HTTP %s" % exc.code) from None
        except (urllib.error.URLError, OSError) as exc:
            raise DeliveryError("CallMeBot send failed (%s)" % type(exc).__name__) from None
        except (ValueError, http.client.HTTPException):
            raise DeliveryError("invalid request") from None
    return send


# ------------------------------------------------------------ orchestration

@dataclass
class Outcome:
    status: str                   # dry_run | skipped | sent | failed
    subject: str = ""
    body: str = ""
    attempts: int = 0
    marked: int = 0
    note: str = ""
    refs: tuple = field(default=(), repr=False)


def _retry(fn, attempts, sleep, delay):
    last = 0
    for n in range(1, max(1, attempts) + 1):
        last = n
        try:
            fn()
            return True, n
        except DeliveryError:
            if n < attempts and sleep is not None:
                sleep(delay)
    return False, last


def deliver_digest(articles, events, now, *, settings=model.Settings(), enabled=False, sender=None,
                   mark_sent=None, attempts=3, sleep=None, delay=30, skip_when_empty=True):
    """Build the digest; if enabled and a sender is supplied, send it and only
    after a confirmed send call mark_sent(refs). A failed send marks nothing,
    so the items appear again in the next digest (geonews behaviour).
    Retry: up to `attempts` (geonews scheduler used 3 x 30 s); `sleep` is an
    injected callable, None means no waiting (no timers in this module)."""
    d = render.build_digest(articles, events, now, settings)
    if skip_when_empty and not render.should_send_digest(d):
        return Outcome("skipped", d.subject, d.html, note="nothing new and nothing critical", refs=tuple(d.refs))
    if enabled is not True or sender is None:
        return Outcome("dry_run", d.subject, d.html, note="delivery off or no sender; nothing sent, nothing marked",
                       refs=tuple(d.refs))
    ok, n = _retry(lambda: sender(d.subject, d.html), attempts, sleep, delay)
    if not ok:
        return Outcome("failed", d.subject, d.html, attempts=n, note="send failed; nothing marked", refs=tuple(d.refs))
    marked = 0
    if mark_sent is not None and d.refs:
        try:
            mark_sent(list(d.refs))
            marked = len(d.refs)
        except Exception:  # the mail is out; never report it as failed (would be re-sent)
            return Outcome("sent", d.subject, d.html, attempts=n, marked=0, note="mark failed", refs=tuple(d.refs))
    return Outcome("sent", d.subject, d.html, attempts=n, marked=marked, refs=tuple(d.refs))


def deliver_critical_alert(articles, now, *, settings=model.Settings(), enabled=False, sender=None,
                           alerted_refs=(), mark_alerted=None):
    """geonews send_if_critical: CRITICAL items created in the last
    critical_lookback_hours, best first; no items -> nothing built or sent.
    DELIBERATE DEVIATION: geonews had no 'already alerted' flag and re-alerted
    the same items on every check in the window. Here the caller supplies
    alerted_refs (refs already alerted) and a mark_alerted(refs) callback that
    is called only after a confirmed send. Items without a ref cannot be
    tracked and are never alerted."""
    seen = set(alerted_refs or ())
    items = [a for a in model.critical_since(articles, now, settings.critical_lookback_hours)
             if a["ref"] and a["ref"] not in seen]
    if not items:
        return Outcome("skipped", note="no new critical items in window")
    subject, body = render.build_alert(items, now, settings)
    refs = tuple(a["ref"] for a in items)
    if enabled is not True or sender is None:
        return Outcome("dry_run", subject, body, note="delivery off or no sender", marked=0, refs=refs)
    try:
        sender(subject, body)
    except DeliveryError:
        return Outcome("failed", subject, body, attempts=1, refs=refs)
    marked = 0
    if mark_alerted is not None:
        try:
            mark_alerted(list(refs))
            marked = len(refs)
        except Exception:
            return Outcome("sent", subject, body, attempts=1, marked=0, note="mark failed", refs=refs)
    return Outcome("sent", subject, body, attempts=1, marked=marked, refs=refs)


def deliver_weekly(articles, now, *, settings=model.Settings(), enabled=False, sender=None,
                   attempts=3, sleep=None, delay=30):
    subject, body = render.build_weekly(articles, now, settings)
    if enabled is not True or sender is None:
        return Outcome("dry_run", subject, body, note="delivery off or no sender")
    ok, n = _retry(lambda: sender(subject, body), attempts, sleep, delay)
    return Outcome("sent" if ok else "failed", subject, body, attempts=n)


def deliver_chat(kind, articles, events, now, *, settings=model.Settings(), enabled=False, sender=None):
    """kind: 'telegram' or 'whatsapp'. sender(text)."""
    if kind == "telegram":
        text = render.build_telegram_message(articles, events, now, settings)
    elif kind == "whatsapp":
        text = render.build_whatsapp_message(articles, events, now, settings)
    else:
        raise ValueError("kind must be 'telegram' or 'whatsapp'")
    if enabled is not True or sender is None:
        return Outcome("dry_run", kind, text, note="delivery off or no sender")
    try:
        sender(text)
    except DeliveryError:
        return Outcome("failed", kind, text, attempts=1)
    return Outcome("sent", kind, text, attempts=1)


_REF_OK = re.compile(r"^[A-Za-z0-9_\-:.]{1,120}$")


def parse_mark_request(payload, known_refs=None):
    """Port of POST /mark-emailed validation: {'article_ids': [...]} -> list of refs.
    Raises ValueError on malformed input (geonews answered HTTP 400). If
    known_refs is given, ids outside it are rejected."""
    if not isinstance(payload, dict) or not isinstance(payload.get("article_ids", []), list):
        raise ValueError("invalid article_ids")
    ids = payload.get("article_ids", [])
    if len(ids) > 1000 or not all(isinstance(i, str) and _REF_OK.match(i) for i in ids):
        raise ValueError("invalid article_ids")
    if known_refs is not None:
        ks = set(known_refs)
        if any(i not in ks for i in ids):
            raise ValueError("invalid article_ids")
    return list(dict.fromkeys(ids))
