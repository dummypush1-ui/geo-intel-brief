# Injected Mongo transaction account seam, offline only

MongoAccountStore uses one pre-provisioned geo_intel/accounts_state document
with _id account-state-v1, schema 1, version and bounded state maps. No client,
credential, default environment, runtime selection, index creation or bootstrap
insert. Exact source/write/schema/transaction developer review required; these
booleans do not establish owner permission. Real Atlas session/transaction,
free-tier support, role and source capability remain unverified until Push
allows a live check. No live Mongo operation occurred in this increment.

Single document stores at most 50 users, 500 sessions, 10000 attempt records,
1000 invites and 50 settings, at most 2MB JSON/100000 nodes/depth16. This is a
bounded small-account design, not a normalized collection migration or scalable
account database. Serialization/write contention on one document is deliberate.
Missing or malformed state fails closed; no automatic schema repair or init.
The operator must separately review provisioning and any future migration.

Every AccountStore operation starts an explicit snapshot/majority transaction,
finds state, reuses original MemoryStore operation on copied maps, validates
bounded result state, conditionally replaces matching version and commits.
Read-only operations also transact. No with_transaction automatic retry, callback
runs once; commit failure is outcome unavailable, may have committed, do not
retry. Abort/end cleanup best effort, fixed redacted error with no source context.
Nested same-thread calls refused. Client externally owned. max_commit_time2s
and find max_time2s aren't total socket/worker deadlines; injected client must
have independent finite socket/connect/pool settings.

Existing atomic semantics preserved for invite+cap+username, session password
version, live-session fences/settings CAS/delete/password replacement. Caller
session retained on password replacement as original; others revoked. One
AccountService/Limiter per store remains required. This does NOT fix existing
multi-limiter/process compensation defect, crash settlement or service session
creation versus limiter-success failure coupling. No account HTTP activation,
TTL cleanup schedule, invite expiry, secret storage or recovery UI added.

8 focused fake-transaction tests: shared backing state across adapter instances,
invite cap/no burn, password/session/settings/delete fences, callback once/nested
refusal, four-thread same-user race, bad state refusal, commit-failure rollback
and cleanup. Fake commits implement locks and rollback; they do not prove actual
Mongo transaction behavior or commit uncertainty reconciliation. Real PyMongo
4.8.0 read/write concern objects used, no fake imported driver. Full existing
account conformance suite not rerun in partial tree; passing is scoped evidence.
Repro python -m unittest tests.test_mongo_account_store -v with PyMongo4.8.0 and
integration/accounts modules. Bundle contains all dependencies, no original
Finder or connected DB needed.

Choice sources inspected:
https://www.sqlite.org/wal.html (same-host/no network filesystem WAL)
https://sqlite.org/atomiccommit.html (transaction atomic commit)
https://www.mongodb.com/docs/atlas/reference/free-shared-limitations/
The user's single Atlas DB direction favors injected Mongo over local SQLite;
no inference about current tier transaction support from these docs.

V2 cleanup uses injected clock (default time.time); expired attempt records and
exhausted invites purged inside transaction before new mutation/bounds. Active
attempt keys still cap10000; refuses limit/invalid distinctly, no eviction of
active brakes. Invites have no expiry format yet;1000 active invite cap permanent
until consumed or separately removed. Deterministic state bound/non-JSON errors
raise MongoStoreInvalid, not an uncertain outage. Control KeyboardInterrupt/
SystemExit re-raised after abort/end cleanup.13tests include10000expiredkeys,
51stuser/nonJSON, sameinvite4thread2winner race and labelled fake OperationFailure
112 WriteConflict/TransientTransactionError plus UnknownTransactionCommitResult.
Each callback executes once; fake rollback doesn't prove real unknowncommit
outcome, recovery/source reconciliation and live support still open. No app retry.

Final review SAFE v2 (13/13 with stub concern types in reviewer environment);
author tests use installed native PyMongo4.8.0.15 final local/extracted tests.
All non-Exception BaseExceptions re-raised after cleanup, including cancellation
and generator exit. Pure get_user/get_attempts/get_settings never persist purge.
Mutating operations drop expired or missing-expires attempts like MemoryStore;
non-numeric expires remain invalid/unsupported producer state. Store clock,
not service clock, governs housekeeping: inject the same clock or account for
skew; a fast clock can expire limiter records early. end_session failure after
successful commit returns unknown/do-not-retry; committed writes may stand.
