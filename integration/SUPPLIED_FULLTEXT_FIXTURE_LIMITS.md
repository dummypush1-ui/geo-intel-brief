# Supplied-text enrichment preparation only

Separate private supplied-text fixture; no HTTP/source fetch, real extractor,
trafilatura import, thread, env/config/DB/log/Telegram/send/durable backup.
Pins RSS/extract exact bytes, inspect exact function definitions/nested process
with name/attribute allowlists; only tiny builtins len/list/Exception supplied.
No original module imports. Pinned64 document seam/dependencies run only after
complete input/output validation. Source pins/AST checks are reviewed drift
controls, NOT hostile-code sandbox or loaded-module authentication.

Original enrichment threshold strictly<200 characters. Nonempty provider result
is stripped, truncated to max_chars then'...' when longer, including replacing
with shorter text. Whitespace-only returns empty. Empty/error download skips
extract; empty/error extract retains original summary. Unavailable/disabled
zero calls. Opaque supplied download handle is URL, not downloadedHTML/parser
proof. Real requests/timeouts/SSRF/parser and live-provider semantics untested.

Declarative outcomes exact download=text|empty|error,extract=text|empty|error,
text bounded plain string. Nontext download requires empty extraction/text;
nontext extraction requires empty text. Missing requested or unused outcomes
reject before AST/provider execution. One supplied outcome per exactURL, but
repeated short-summary candidates call download/extract EACH time in order,
never cache/dedupe before enrichment. Trace is ordered calls+URL+occurrence;
no actual fetch/authenticity evidence or credential/config fields. Original64
then dedupes titles/classifies/prepares docs. Synthetic IDs, emailed/save/mark
receipts not created. Original empty Telegram placeholders retained, not sends.

Up to100 exact closed candidate records with title/url/source/summary/published/
credibility; fixed-offset exact aware datetime, UTC year1970..2100. Exact strings
<=10000,URL<=2000, title/URL already stripped. Exact category controls1..100 characters, <=20;
exact boolean enable/availability and positive exact max_chars<=9997 (output
<=10000 including ellipsis), finite threshold0<value<=1. These are narrower
than all possible original inputs, not blanket collector parity. Scalar and
container subclasses/hooks refused; no caller provider/executor/callback/store.
No caller overrides/unknown fields. UTC boundary checked before publication.

Snapshot and whole-batch validation before AST/provider/doc seam; cheap field
counts,5000nodes,1MiB aggregate UTF8 for inputs and separately combined returned
candidate/trace/doc output. Input and output each bounded, not combined1MiB.
Out-of-range/invalid UTF8/date/config/outcome or output growth refuses whole
composition, no partial published result. CPU/allocations remain bounded-input
research, not process timeouts or hostile memory isolation. Same output result
contains independent candidate/doc dictionaries; immutable date/string reused.
Returned text is private SUPPLIED data, not fetched/verified/lossless full article.
Stored original doc preview<=300; Telegram full-content preservation remains
unwired, neither silently dropped nor proved by this preparation.

11author focused tests include independent original AST oracle with separate
provider/executor mocks,199/200/201, repeats/order/isolation, disabled/unavailable,
empty/error/short/whitespace/Unicode strip/astral/exactlimit/ellipsis, aggregate
input/output growth, malformed whole batch/no hooks, drift and no newly imported
original/external modules. No HTML/mail/UI artifact, no visual readiness claim.
Full configured suite and independent code review pending.
