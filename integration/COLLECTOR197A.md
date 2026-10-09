# 197a: injected durable collector orchestration

Source-only, unmounted and default OFF. No production facade or entry change.
GEO_WRITER_MONGODB_URI is a new contract name, not a deployed writer connection.
Never falls back to GEO_MONGODB_URI or MONGODB_URI. Fixed geo_intel.articles,
geo_intel.collector_jobs197 and geo_intel.collector_checkpoints197 mappings.
Actual collection identity and live role/index/TTL evidence are 197b obligations;
this unit accepts assertions, not proof. Initialization/provisioning is NOT run.

One accepted→running CAS winner enters fetch. Durable majority+journal ledger
and checkpoint handles are required. Immutable capture/checkpoint is stored at
running before prepare. Only prepare_complete→write_started CAS permits the
injected GeoArticleWriter. Partial, unknown, malformed or unacknowledged writes
remain locked for reconciliation. Replays never resume fetch/write. Expired
leases never transfer; retained 64-job history fails closed when full. No
automatic retries, takeover, article TTL, index creation, archive or recovery.

90-second whole-cycle contract is below 120-second lease. Per-feed bound is
25 seconds. Runtime guards reject overrun before/after injected fetch and
before write. They cannot kill a blocked callback and are NOT hard supervision.
197b must provide hard wall supervision/kill/reap, fixed catalog and network
header parity, real Mongo identity/role/index/no-TTL probes, bounded driver
write timing, authenticated owner POST /api/collect with durable request ID,
client lifecycle and production wiring. No live activation without owner OK.

Checkpoint capture remains at most 2 MiB/20,000 nodes/1000 candidates. Network
aggregate ≤4 MiB and its process input/output accounting belong to 197b.
No mail, Telegram, fulltext/GNews, import-time timers or old collector changes.
The currently held public read application continues unchanged.
