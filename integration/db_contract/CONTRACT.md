# Database resources, indexes and retention proposal

Copyright (c) 2026 Push. All rights reserved.

No provisioning, client, DB write, delete, role, index, TTL, mount or activation.
Exact collector names must be coordinated before executable schemas. Tests use
fixture names, not approved live collection names. plan() takes explicit distinct
names for full_records, collection_outbox, collection_control and backup_journal.
Fixed existing mail/article resources stay geo_intel/articles/events/mail_control/
mail_receipts. Output is a candidate, not an authorization or persistence claim.

## Privilege boundary

Separate proposed publicreader, mailworker, collectionwriter, backupjournalworker.
Each grants explicit collection actions only (find/insert/update), no inherited
readWrite/admin role, createIndex, remove, drop, rolemanagement or cluster action.
Provisioning credential is separate and not modeled as a runtime role. Existing
read-only facade remains intact. Mongo role updates are collection-level, not
field-level: mail article update can modify more than emailed flags. Application
validation, isolated credential, transactions and actual role audit still matter.
Backupjournalworker has no article access. It records acknowledgements in its
journal/outbox; collectionwriter publishes preview Telegram references only
after authenticated complete-receipt validation. That publisher is a later
implementation, not assumed present.
These proposals are not proof that an Atlas free tier exposes custom role APIs or
that deployed accounts have only these privileges. Verify current account/tier.

## Index candidates, not executed

Unique articles.url requires existing duplicates/index/collation review first.
Unsent emailed+score+published+_id compound index, created_at, events.event_date,
mail_receipts channel_id+created_at are candidates for query explain/storage-cost
review. None is TTL. Existing implicit _id indexes support exact receipt/control
keys. Do not create duplicate/conflicting index names blindly. No guarantee that
a compound query candidate is optimal without real explain/index inspection.
Collector schemas/indexes remain interface requirements pending exact mappings.

## Runtime140handoff compatibility

handoff.prepare output is untrusted candidate data with all authority/durability
flagsfalse. Batch/record hashes bind bytes, not author, storage or recovery proof.
Retain full_record losslessly beside summary300 preview, not in the same TTL
lifetime. Commit preview+fullrecord+checkpoint/outbox transactionally with reviewed
version/lease fencing. Existing GeoArticleWriter unordered preview insert is NOT
that atomic commit and must not be reused as if it preserves fulltext/outbox.
AgentA owns the collector engine/fulltext/GNews/Telegram journal implementation.

The collection send journal must bind exact destination, record/batch/piece
payloadhash, attemptnonce+version and providerack. Record sending durably before
effect, unknown timeout/disconnect latches. Every required piece needs current
authenticated receipt before completebackup. Local MAC/hash fixtures cannot
prevent rollback/replay or prove provider acknowledgement. This proposal performs
no sends or receipt verification and cannot unlock a collector lease.

## Retention and TTL

No TTL on articles, fullrecords, pending/active mail receipts, collectionoutbox,
control or backupjournal. No automatic deletion anywhere. Terminal supplied
fullrecord+allpieceauth+export claims merely make a record eligible for owner
retentionreview; delete/TTLallowed remainfalse. Unknown/pending alwayshold.
Actual archiveexport/recovery evidence and ownerapproval required separately.
Never delete receipt keys while replay/newnonce could resend an old effect.
Save135mailarchive128cap is unchanged; operator must see failclosed and plan an
explicit reviewed retention/export solution, not enableTTL as a quick fix.
MongoTTL uses a backgroundprocess and BSONdates; ISOstring articletimestamps
are not equivalent expiry fields. No source-specific TTL or migration selected.

## Official source grounding (fetched October8,2026)

https://www.mongodb.com/docs/manual/core/security-user-defined-roles/
Customroles described with explicit privileges; actual Atlas availability unverified.
https://www.mongodb.com/docs/manual/reference/privilege-actions
find/insert/update apply to database/collection resources. Role is not field policy.
https://www.mongodb.com/docs/manual/core/index-ttl/
TTL is a special single-field automatic expiration index; background cleanup,
not a receipt-aware transaction or exact-clock retention guarantee.

## Delivery status

11puretests, proposedroles/indexes/retentiondecision only. No installed DB roles,
no schema/provisioning command, no durable writer, no completebackup claim.
Default-off routes and containment gate remain unchanged. Mail routing/credential
binding and production retention implementation remain later reviewed units.
