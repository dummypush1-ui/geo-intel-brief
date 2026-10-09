# 197b composition candidate, not live activation

Mongo preflight executes read-only connectionStatus(showPrivileges), hello and
bounded exact collection listIndexes; it creates no clients, collections,
indexes or ledger documents. Requires one authenticated principal, writable
replica set primary, exact collection grants: articles find/listIndexes/insert,
jobs find/listIndexes/update, checkpoints find/listIndexes/update/insert. All global, database-wide and
extra grants refuse. It uses majority read and majority+journal writes.
Rejects any TTL on any of the three collections and requires a full unique
url:1 index, no partial/sparse/non-simple collation. Existing geo108 ledger
fingerprint/schema must match. These are observed capabilities, not permission.

Sources:
https://www.mongodb.com/docs/manual/reference/command/connectionStatus/
https://www.mongodb.com/docs/manual/core/index-partial/
https://www.mongodb.com/docs/manual/reference/read-concern-majority/

Parallel-four fixed 25-feed AST catalog, 90-second whole-cycle contract,
70-second fetch cutoff with explicit failed/unstarted sources. Each body read
is capped at 1 MiB before reading; JSON-line byte telemetry includes refused
feeds. Conservative 1 MiB launch reservations fit the 26 MiB cycle ceiling.
Wire accounting is response BODY bytes, not TLS/header/framing overhead.
Malformed telemetry/cap errors refuse a source; incomplete result envelopes
never yield candidates. Decoded aggregate also at most 26 MiB; candidate
capture remains 2 MiB/1000 rows. REQUEST_TIMEOUT follows original installation
profile; combined per-feed fetch/parse/selection is at most 25 seconds.

Every feed is in a bwrap PID namespace with die-with-parent and no new session;
all supervisors stay in coordinator process group. Individual timeout kills
the namespace supervisor; kernel kills descendants. Wrapper SIGTERM/grace then
SIGKILL group also kills every namespace. Actual fixture process cutoff and
forced coordinator kill tests inspect no remaining unique host process marker.
Fixed parser remains in separate network-less bwrap namespace, no fallback.
Four 256 MiB child limits are not a 512 MiB deployment capacity proof. Actual
Render kernel/bwrap and free capacity must be independently verified first.

Explicit owner-only default-OFF factory is unselected. No production facade
or live switch is changed. Enabled construction requires injected runtime
preflight, then read-only Mongo preflight; source assertions are not owner
permission or actual Render proof. Routes authenticate Bearer before ledger;
no browser Origin/query allowed, strict nonce/timestamp JSON. No import-time
work, timers, index/collection/ledger provisioning, mail or old collector stop.
Source status is response-only here. Durable coverage and production mounting
are deliberately deferred to 197c; this is NOT live-ready merged collection.

Conservative collation gate requires explicit locale:simple index metadata.
Older servers may omit that field for simple indexes; missing field refuses
rather than pretending it proves collation. Source evidence:
https://jira.mongodb.org/browse/SERVER-92900
https://github.com/mongodb/mongo-python-driver/pull/2761
No actual Atlas/server durability, role, deployment or free quota was tested.
Configured majority+journal concern is not a successful durable-write proof.

