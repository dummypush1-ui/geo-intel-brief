# Collector dependencies/security preparation

No package downloaded/installed, source fetched beyond authorized repository
reads, parser run on external RSS, or live collector executed by this plan.

Separate worker lock: do NOT expand public requirements-staging implicitly.
Core: requests, feedparser, python-dateutil, pymongo, dotenv. schedule not needed
if AppsScript/queue/Rendercron is sole scheduler; optional trafilatura/GNews and
transitive XML/network packages separately reviewed only if original enabled.
Original floating >= requirements are source description, not chosen safe pins.
Preserved old locks include vulnerable versions and are NOT security-clean.

For chosen profile: resolve supported Python/OS + exact source-compatible fixed
versions from upstream advisories, verify official wheel hashes/METADATA/tags/
active dependencies, complete hashlock and fresh offline install/pipcheck. Do
not use absent optional dependency as silent feature drop. Snapshot source and
SDK physical pins; compare original classifier/date/dedupe/schema outputs over
representative bounded fixtures. Timezone/date backend regression included.

Network/parser boundary: new arbitrary XML ingestion cannot reuse fixed corpus
runner as if general sandbox. Need compressed/decoded-size budgets, CPU/AS/wall/
output cap, kill-group/reap, redirect/DNS/privateIP/HTTPS policy, deterministic
source allowlist. Fulltext/GNews add separate attack/sourcepolicy surfaces.
Validate rows before writer; no nested stringify, fixed schema/aggregate limits.
No email/Telegram/server-side templating credentials inherited by parser child.

Job/token boundary: require auth before network/DB, header secret never query,
strict bounded request, no caller source/collection/URI/module/recipient. Nonce
replay idempotent, durable ownership/fence/lease/status in reviewed jobs store.
In-memory FixtureLedger is ONLY a contract model, cannot deploy as durability.
Failure after write start is uncertain, not retry-safe. Index and driver errors
must prove exact URLduplicate; code11000 alone insufficient. No automatic
index creation/deletion/cleanup or sent marking. Source exception messages,
stacktraces/URLs/credentials never in publicjob responses or logs.

Non-live migration decision list:
1. Topology: AppsScript+paidqueueworker / Rendercron / restartablefreeweb.
2. Full original behavior scope: RSS/GNews/fulltext/events/Telegrambackup flags.
3. Writer/read separation, exact article/index and durable jobs-store role.
4. New collection-only ScriptProperty/adapter/cadence; mailbase unchanged.
5. Actual triggers/services inventory BEFORE cutover and precise rollback.
6. Manuallivefetch/write scope then switch/oldstop separate ownerapprovals.
