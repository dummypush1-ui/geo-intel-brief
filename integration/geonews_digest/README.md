Copyright (c) 2026 Push

# geonews_digest (digest, critical alert, weekly summary, chat digests)

Port of the report behaviour of the public repo `push2006/geonews` (commit d0937ab66c20122cbd33e7385ec577914c506c73, 2026-09-22) as pure modules. Selection rules, ordering, limits, thresholds, section order, wording and colours follow the original; see the table below for the few deliberate differences.

Standard library only. No database, network, timers or file/env reads at import or in the build functions. Delivery code (SMTP mail, Telegram Bot API, CallMeBot WhatsApp) is present in `delivery.py` but OFF: nothing is sent unless the caller passes `enabled=True` (exactly `True`) and supplies credentials as arguments and a sender. Default calls return a dry-run `Outcome` with the subject and body and mark nothing.

## Interface
- `normalise_all(rows) -> (articles, stats)`: accepts the legacy geonews row shape and the public news shape; drops unknown keys (telegram_*, backup_url, ...); https links only; aware dates only; bounds on every value.
- `build_digest(articles, events, now, settings) -> Digest` (`.html`, `.subject`, `.critical_count`, `.refs`, `.to_digest_data()` = the `/digest-data` JSON shape), `should_send_digest(d)` (Apps Script skip rule).
- `build_alert(items, now)`, `model.critical_since(...)`, `build_weekly(articles, now)`, `build_telegram_message(...)`, `build_whatsapp_message(...)`.
- `deliver_digest / deliver_critical_alert / deliver_weekly / deliver_chat(...)`: build, and only with `enabled=True` plus a sender, send; the digest marks items sent via your `mark_sent(refs)` callback only after a confirmed send; failed sends mark nothing. Retry count and an injected `sleep` replace the original 3 x 30 s loop (no timers here).
- `parse_mark_request(payload, known_refs=None)`: validation for the `/mark-emailed` call.
- `smtp_sender / telegram_sender / whatsapp_sender(enabled=..., credentials...)` -> sender closures. Errors never contain tokens, passwords or URLs.
- `Settings`: defaults equal geonews (min score 4, 60 per digest, 90 upcoming days, 6 h critical lookback, 7 days / 20 items weekly, 8 countries, 8 and 6 chat items). `display_tz` defaults to Asia/Kolkata and every printed date states its zone.

## Deliberate differences from geonews
| Area | geonews | Here | Why |
|---|---|---|---|
| Links | any URL, only HTML-escaped | https only, default port, no credentials | `javascript:` etc. cannot reach mail |
| Dashboard link | `?key=<TRIGGER_SECRET>` in mail and Telegram | plain https URL only; secrets are refused | secret in a message is a leak |
| Telegram text | raw Markdown | `_ * ` [ \` escaped in titles/names | a title with `_` or `*` makes the API reject the message |
| Dates | server local time, no zone | caller `now`, zone shown | owner rule: dates carry the time zone |
| Data source | MongoDB queries | caller supplies rows; queries re-implemented as pure functions | no live DB in this stage |
| Empty weekly top list | prints an empty heading | adds "No items in the supplied data... does not mean nothing happened" | do not read silence as quiet |
| Weekly ties | Mongo leaves ties unordered | ties sorted by name | deterministic output |
| Recipients/subject | not validated | recipients validated, CR/LF in headers rejected | header injection |
Everything else (sections, labels, risk and credibility colours, "confirmed by N sources", critical count, event block, footers) is the same text.

## Deliberate behaviour changes (review round 2)
- Digest: items below min_score are dropped BEFORE the 60 cap, so the refs marked sent equal the items shown. (geonews capped first and marked unseen low-score items as sent.)
- Critical alert: the caller supplies `alerted_refs` and `mark_alerted(refs)`; items already alerted are skipped and refs are marked only after a confirmed send. (geonews re-alerted the same items on every check in the 6 h window.) Items without a ref are never alerted.
- If marking fails after a confirmed send the outcome is `sent` with note `mark failed` (never reported as failed, which would cause a re-send).
- Telegram: token/chat id format-checked at construction; malformed requests become `DeliveryError('invalid request')`; URLs are escaped (`_ * \` [`, `)` as `%29`); long messages are cut at a line boundary.
- Bidi/format characters (U+2066-2069, U+061C, U+180E) are stripped from text. Missing zone database falls back to fixed +05:30.

## Still as in geonews
- Chat digests take the best 60 by score, keep score >= 4, then the first 8 (Telegram) or 6 (WhatsApp).

## Not ported (out of this module's scope, see PATCH.md)
Collectors, classifier and dedupe (other merged modules), Telegram full-record backup/archive and Mongo metadata cleanup (destructive), dashboard and CSV routes, the scheduler loop and Apps Script triggers (timers), digest archiving to disk (the caller can store `Digest.html`), config check.

## Checks
`python -m unittest discover -s tests/geonews_digest -t .` (34 tests). A development-only parity script (not shipped in this bundle) ran geonews' own database and report code on an in-memory Mongo fake and compares what is selected, its order, counts, section order and the chat texts with this module: all pass for the 150-row fixture. Not checked: how the HTML looks in a mail client.
