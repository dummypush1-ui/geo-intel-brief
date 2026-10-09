# Native 200b-c: separately selected automated admission

Adds NEW admission store/preflight/journal/core/adapters, with old 199, 200a,
200b-a and 200b-b bytes unchanged. No production composition selects them.
Default OFF, explicit injected client, no env reading, provisioning, migration,
Atlas request, transport effect, workflow edit or live cutover.

The extended validator is a distinct reviewed schema, inspected only. Existing
outcome shapes remain accepted, plus a discriminated immutable admission record
in native_outcomes200. No ninth collection. Guards add admission_attempt.
Old preflight intentionally rejects the extension, and old exact adapter gates
reject the new core. Schema installation/maintenance is a separately authorized
gate-2 activity; this code does not install it.

Admission only from acknowledged with capacity remaining. A read-only snapshot
verifies the full chain/source and the exact prior immutable intent/outcome.
The current source hash must equal the old outcome, and the next plan's revision,
epoch and head must match. Majority+journal CAS first permanently latches
acknowledged-old -> admission_attempt, retaining old operation/serial. A fresh
native transaction re-proves the same source and exact latched guard, then
atomically CASes reserved-new, inserts the immutable successor intent, and
inserts an immutable admission record binding old/new operation IDs/serials
and the proven source hash. Readback happens inside that same transaction.

Only its same-process known commit ACK returns an executable successor intent
for the source-write transaction. Unknown/lost ACK never returns that intent.
A failure before commit leaves admission_attempt held; a committed but unknown
admission leaves reserved-new held. No idle release, retry, reclaim, compensation,
TTL, delete or restart execution exists. reserved/commit_attempt cannot admit.

Accepted consequence: a crash after acknowledged admission but before successor
execution permanently holds the source until owner review. Read-only restart
reconciliation labels this admitted_but_never_executed_owner_review_required.
The same observation also covers a landed admission whose ACK was lost: it does
not assert the ACK was received or distinguish that historical fact. Latch-only
and malformed admission records have distinct held states. None clears holds,
grants retry, or claims recovered capacity. Future restart recovery is excluded.

First idle guard reservation uses the original 200b-a ordering. All later source
writes still use its journal-before-write-begin, same-txn sourceCAS/outcome marker,
commit_attempt-before-singlecommit, and acknowledged-but-not-idle semantics.
Read-only no-change replay remains status only. The local lock is process-local;
the durable guard CAS is the cross-process stop. Concurrent external writes cause
loud refusal. Guard serial caps at4096 and is never reset.

Pinned4.18.2 synthetic loopback tests cover multi-step collector/broker workflows,
admission wire errors/lostACK, crash-before-execution, exact atomic session/txn,
missing proof and capacity. They do not prove actual MongoDB isolation, validator
enforcement, replication or crash durability. Restricted no-creation role plus
verified schemas/indexes/DDL boundary still required. Real measurement/cadence
activation needs separate gates and explicit owner live approval.

## Superseded gate2 role claim

The earlier no-creation-role requirement above is superseded by
NATIVE201GUARD.md: INSERT itself can permit implicit collection creation.
The operational role is least-privilege, NOT creation-proof. All-eight exact
validator preflight, owner-exclusive DDL boundary and an accepted one-write
inspection/insert TOCTOU effect replace that claim. No zero-effect guarantee.
