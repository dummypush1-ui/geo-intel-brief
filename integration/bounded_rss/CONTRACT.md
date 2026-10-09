# RSS177 bounded legacy seam (held by default)

The legacy RSS requests/feedparser names now point to one bounded driver, not
requests.content or an in-process feedparser. Import builds only a held driver,
never fetches. Explicit installation can construct an enabled driver with exact
reviewed feed tuples and projection1..200; mounting it and starting collectors
remain separate owner/runtime steps. Default catalogue unchanged25feeds. Custom
extras do not bypass installation. No unsafe fallback, no artificial dates.

Fixed124transport caps wire/decoded1MiB, streaming chunks64KiB, verifies every
DNS answer/public peer/TLS hostname, refuses redirects and bad framing, kills
and reaps its worker at deadline. Fixed128parser uses no-network bubblewrap,
pinned SDK6.0.11, memory256MiB/CPU3s,1MiB input/output and512KiB projected text.
Two phases share min25s/configuredtimeout. This is a phase budget, not a claim
of hard aggregate cycle/supervisor memory or wall containment. Dense XML,
non-UTF8, malformed/bozo, isolation absence and oversized entries are refused.

The original field/date selection is unchanged over a one-use opaque parsed
projection, never a parser URL or raw stream. Output errors are a fixed safe
source_refused label, without raw source names, URLs, query keys or exceptions.
A refusal yields zero candidates, NOT proof of a healthy source. Installation
health/status, full cycle supervisor, resource sizing, fulltext extractor and
live wiring remain held. Fulltext original still defaultOFF and unsafe to enable.

Historical117dependency-pins.json stays untouched; current supplied-cycle
preflight uses new dependency-pins177.json. Original108 inventory/reconciliation
stays source evidence; current consumer pins are explicitly refreshed only after
review of original selection/document differential tests.
