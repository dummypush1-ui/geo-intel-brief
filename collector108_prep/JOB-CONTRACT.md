# Proposed collector job contract, inactive preparation

No route/runtime/trigger installation. To review before implementation:

Request: authenticated POST with fixed collection profile/version, opaque
request nonce, created-at UTC. No caller-provided sourceURL/collection/URI/
code/module/classifier/send recipient. Header token secret never URL/log.
Canonical serviceorigin fixed; body<=4096 bytes, nonce grammar/length strict.
Reject omitted token, malformed body or flags before client/network creation.
Replay nonce returns prior job identity/status, not another collection cycle.

Durable store: exact reviewed jobs collection, unique nonce/profile key, atomic
claim with fencing token/lease/expiry, one active profile at a time across
workers/services. Time expiry alone must not enable double writes if old job is
still executing: separate renewal/stop/reconciliation. Single worker lock is
not substitute for durable ownership. Restart outcome marked interrupted or
unknown, never success. Job source/settings fingerprint immutable.

Statuses: accepted, running, fetch_complete, prepare_complete, write_started,
completed, refused, failed_before_write, uncertain_after_write, interrupted.
Count bounds captured each phase, no article content/URI/token/exception text in
public logs. Status endpoint authenticated; aggregate source/job counts only.
Write-start phase may not be blindly retried. Bulk duplicateURL receipt only
when exact unique index and driver keys prove it. Unique index is external
current-state verification, not fabricated test assumption.

Source contract: fixed reviewed original RSS list + explicit extra-feed catalog;
future GNews/events/Telegram flags scope recorded. Network client rejects
unsafe/local DNS/redirects; strict TLS, bounded decoded/compressed bytes,
wall/read/connect budgets, max concurrent tasks/output. XML parser needs actual
arbitrary-input resource boundary, not only reviewed fixed synthetic corpus.
Fulltext same bounded allowlisted networking/parsing. Preserve original
classification/date/score/country/dedupe/document semantics with differential
fixtures. Source-policy and remaining transport gaps are separate blockers.

Scheduling: AppsScript collection-only wrapper to separate collectorbaseURL,
header-token property, strict HTTPstatus+job receipt validation, no new trigger
installer until actual schedule ownership confirmed. Original mail/checkCritical/
weekly/cleanup trigger functions retained until each separately migrated.

Deployment: owner-approved Render job/worker/topology after current pricing and
lifetime constraints researched. No ephemeral daemon thread assumed durable.
Only one scheduled owner after explicitly-approved cutover. Rollback disables
newjob triggers and restores oldcollection trigger; uncertainwrites reconciled.
