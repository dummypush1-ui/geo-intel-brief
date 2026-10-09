# Native 201a: atomic immutable checkpoint and source advance

New NativeCoverageCheckpoints exposes validated get only, no standalone put.
It accepts the exact AdmissionStore collector_checkpoints197 mapping and keeps
existing typed-budget, encoded schema, input hash and source-coverage hash
validation. checkpoint_row is pure preparation, not a database mutation.

New NativeCheckpointCollectorLedger adds checkpoint_and_advance. A read-only
complete-chain/source view verifies the exact running key/fence, lease/clock,
bounded inputs/coverage and any existing immutable checkpoint. A conflict refuses
before admission. A journal plan precedes a fresh source-write transaction. In
that ONE transaction, absent checkpoint is inserted via raw no_reauth and read
back exactly, then source is CASed running -> fetch_complete and read back. The
inherited source outcome marker is in that same transaction. Existing identical
checkpoint is verified, never rewritten. No upsert, replacement, TTL or deletion.

Admission and source commit semantics remain unchanged: latch before admission,
known same-process admission ACK only, journal before source mutation, no retry,
no idle release, and unknown outcomes held across restart. Checkpoint presence
alone never grants permission to resume a job or redo fetch/write work.

Existing 199, 200a, 200b-a/b/c bytes and exact gates unchanged. New ledger and
coverage types are unselected; no collector cycle/composition accepts them yet.
No live flag, production selection, env/client creation, workflow, provisioning,
Atlas request, timer or article write is included. Source-only/default OFF.

Pinned4.18.2 loopback fixtures exercise shared lsid/txnNumber for checkpoint,
sourceCAS and marker, real391 single-frame failures and unknown commit, immutable
scope, wrong ticket/clock/lease, replay of identical checkpoint and hash corruption.
The fixture does not prove actual Mongo isolation/validators/crash durability.
Gate2 role/schema/index/DDL boundary and gate3diagnostic evidence remain required.

## Superseded gate2 role claim

The earlier no-creation-role requirement above is superseded by
NATIVE201GUARD.md: INSERT itself can permit implicit collection creation.
The operational role is least-privilege, NOT creation-proof. All-eight exact
validator preflight, owner-exclusive DDL boundary and an accepted one-write
inspection/insert TOCTOU effect replace that claim. No zero-effect guarantee.
