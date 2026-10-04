# Source-check observations

SourceHealthSnapshot accepts caller-supplied captured source checks, not a live
collector or status endpoint. No callbacks, requests, storage clients or probes
are added. The private API accepts only this exact snapshot type. Unwired,
unavailable and verified-empty states are different. No current health is
claimed from a stored successful check.

The panel shows observation age, per-source check time, recorded status, fetched
count and safe error-code enums. Raw provider error strings and URLs are not
exposed; they may contain credentials or request data. Source names are rendered
as literal text. A status is historical even when its label is "ok".

Up to100 of1000 supplied source checks are shown; truncation is disclosed.
Counts are source checks, not unique source identities. Only supplied known
project identifiers are accepted; no production source mapping is inferred.
Future observations/checks fail unavailable rather than appearing fresh.
No universal freshness threshold is invented; age is explicit. Manual refresh
rereads the supplied snapshot only. Automatic polling remains disabled.

Preview source checks will remain unwired until a reviewed observation reader
and source ownership/collection schedule are established. This is display prep,
not permission to run a source, change its policy, or write the database.

Unwired returns HTTP200 with state=source_health_unwired, not a successful
empty snapshot. UI displays unknown health, not zero sources. Error codes on
recorded ok checks are rejected as contradictory. Exact string dict keys
prevent subclass-key hooks at this boundary.
