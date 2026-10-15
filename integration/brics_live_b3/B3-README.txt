B3: separate reviewed read-only BRICS stored-news source and public page bridge

Default OFF PUBLIC_BRICS_LIVE_READ_ENABLED=false. Public live builder only.
No change to the existing fixture boundary or public video-wall data/players.
Explicit false and absent have identical route bytes/headers. OFF performs no
source/pin/file read. An unexpected binding while OFF is refused.

ON also requires existing PUBLIC_BRICS_NEWS_ENABLED, PUBLIC_NEWS_READ_ENABLED,
PREVIEW_PUBLIC_SAMPLE_ENABLED and exact BRICS_STORE_MAPPING_VERIFIED,
BRICS_PUBLIC_DISCLOSURE_VERIFIED, BRICS_READONLY_CREDENTIAL_VERIFIED gates.
An exact Binding contains a separate SQLiteReader or MongoReader, Review with
exact source identity and operator evidence references for mapping, disclosure
and readonly privilege, and the reviewed critical-keyword snapshot. These
references and booleans are NOT self-authenticating proof or new permission:
operator must verify the actual source and user's disclosure authority first.
No database/credentials/private source was inspected or enabled for this build.

SQLite adapter opens an existing regular nonsymlink file using URI mode=ro,
query_only,1s lock timeout,2s query progress guard; it never constructs the
original store or creates schemas/indexes. It reads exactly the public columns,
orders collected_at/id descending and bounds to100 rows. SQLite WAL/shared-memory
bookkeeping may occur as normal for a read connection; no article/DB changes
are allowed. The real SQLite synthetic test verifies main DB bytes unchanged.
Mongo adapter takes only the existing read-only facade, explicit separate
reviewed deployment/database/articles identity; geo_intel database is refused.
Projection excludes raw/private/Geo fields; sort collected_at/id, limit100,
batch100, maxTimeMS2000; cursor closes on success/failure. Facade is an accidental
write guard, not proof a supplied credential is read-only or an introspection
security boundary. No URI creation, account access, index or collector import.

Service revalidates exact source identity, reads on manual demand at most once
per60s per process, projects only the existing BRICS fields and applies preserved
BRICS relevance rules. Empty publication strings mean unknown; naive collected
means UTC. Critical keywords require relevance and collected age [0,24h), not
publication recency. Unknown corroboration remains unknown, not cleared; no Geo
risk/credibility terms are introduced. Maximum100 source rows and250000 response
bytes. Unsafe individual stored rows (NULL fields, malformed URL/date or other
projection failures) are skipped and counted as skipped_rows. Zero safe rows
with skipped_rows>0 is not a no-news result. Source/connection/overflow/response
failures still fail closed. No raw row or error is exposed. Failure clears cache, returns503 without private diagnostics, latches until
restart and closes the reader; no Geo fallback/retry. Close is idempotent and
registered at exit. HEAD performs no source read. No raw proof refs/identity,
private fields or credentials enter public responses.

ON replaces only existing BRICS news page/API/asset view functions after their
ordinary public mount. Existing origin/method/query guards and no-store/CSP/
referrer headers remain. New page is manual-only; bounded streaming JSON read,
12s abort, strict closed response/row validation, textContent for source text,
HTTPS external links with noopener/noreferrer. No auto fetch/timer/player/video
load. News clicks do not restart video players. At320px a long literal source
heading first overflowed; fixed with a wrapping safe title link and retested.
Actual Chrome320/390/1100 tests check no auto-read, XSS literal text,60s cache,
source failure clears cards, no retry/player traffic and no page errors.

This connects the separate stored-data read path and page, not full live parity.
Activation still needs real mapping, credential/privacy proof and operator
cutover approval. Source collection cadence/freshness, full-store pagination,
original300-row dashboard parity, source health dashboard/export, owner defaults
management and provider-live availability/recovery remain separate work. No live
BRICS/Geo database, collector, delivery, source API, deployment or flag changed.
