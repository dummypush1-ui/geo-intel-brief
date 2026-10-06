# Supplied parsed-entry feed selection

Private isolated function research, not HTTP/XML/feedparser/provider health.
No original RSS/classifier/config module import, requests/feedparser/thread/env/
DB/Telegram/send. AST only exact pinned _fetch_feed/strip_html/parse_date, explicit
names/attributes; source literal _HEADERS/_ENTITY_MAP and regex expression read
from pinned sources. Tiny Exception/print sink builtins; sink drops raw formatted
source/exception text, returns fixed supplied_source_error code only. Pins are
reviewed-code drift controls, not hostile-code or loaded-object authentication.

One feed exact source/url/credibility tuple/list; exact supplied parsed entries
<=100, closed optional title/link/summary/description/published/updated strings,
no unknown fields or arbitrary objects/callbacks/exceptions. Strings<=10000,
feed scalar<=2000, incremental1MiB UTF8/5000nodes input; same separate output
budget. Invalid UTF8/scalar subclasses/config/date refuse before source execution.
Cutoff/fallback exact fixed-offset aware datetime with UTCyear1970..2100;
max_items exact1..100, timeout finite exact positive<=30. Timeout is only supplied
traced parameter, not a real deadline or external availability evidence.

Original slice BEFORE missing/old-entry filtering; title/link stripped; summary
absent falls back to description, present empty does not. Published absent falls
back to updated, present empty does not. Date equality cutoff accepted. Original
strip_html entities/whitespace retained. Output candidate keys/order unchanged,
no docs/IDs/emailed/save/backup references. URL text supplied, not authenticated
provider/feed identity or vetted safe destination. No source health assertion.

Dateutil version exactly2.9.0.post0. Internal parser facade supplies fixed UTCclock
as naive default for partial date/time components, a documented deterministic
DEVIATION from original real-current-date behavior. Empty date original now
fallback uses fixed clock. Malformed date/UnknownTimezoneWarning becomes fixed
fallback (unknown zone NOT verified UTC), no warning stderr; date_fallback_count
counts parser exceptions/unknown zones, not empty-string now fallback. Full
original date parser catches errors, so this is not parser authenticity proof.
Post-parse normalize only exact datetime with reviewed timezone/tzutc/tzoffset/
tzlocal concrete classes, preserve ISO/instant using fixed offset. Selected date
outside UTCrange refuses whole output. Dates filtered as old are not output and
not reported valid. Real timezone databases/ambiguous abbreviations unverified.

Declarative http_mode/parser_mode ok|error built into exact inert facades.
Opaque bytes handle maps to copied declarative entry list, not actual XML parse.
Errors return original empty candidate list with fixed coarse diagnostic; empty
ok is not healthy/completeness. Strict entry contract cannot trigger mid-loop
partial-source-error semantics, so partial-error parity is NOT claimed. Source
print suppressed; trace contains supplied URL/timeout, never credentials/config.
Caller input untouched, independent copied output rows, immutable dates reused.

10author focused PASS with independent original AST oracle and separate facades/
explicit clock policy; maxslice/filter/equality,absence/empty precedence,HTML,
naive/GMT/+0530/Z/partial/time-only/malformed/unknown-zone dates,source failures,
whole-input/hooks/UTF8/budget,selected-date bounds/drift/no new external imports.
No composition to80, real fetch/SSRF/timeout/XML-parser behavior or UI artifact.
Full configured suite and independent code review pending.
