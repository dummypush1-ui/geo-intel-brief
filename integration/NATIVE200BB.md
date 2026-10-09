# Native 200b-b: additive pair only

New NativeArchivedCollectorLedger and NativeArchivedProxyReceiptBudget inherit
unchanged 199 business methods, but accept only the exact enabled NativeArchiveCore
and override its mutation path. Old 199 exact type gates are byte-unchanged and
continue to reject these new types. No broker/collector/production composition
accepts them. No transport, env/client construction, provisioning, live selection,
automatic rollover, guard release or closure is included.

A nonblocking core-local lock serializes preparation with rollover. A read-only
transaction verifies the full bounded archive chain, validates the method's
business transition, and computes the exact resulting source. A no-change replay
returns status only without a guard reservation. A mutation records an immutable
journal plan, then a fresh native transaction revalidates the complete snapshot
and identical result before source CAS/readback. The core adds the outcome marker
in that same transaction and durably records commit_attempt before its sole
commit. All 200b-a raw bridge, preflight, concerns, no-reauth, capacity, restart
hold and no-auto-release behavior remains in force.

This unit deliberately permits only one mutation per pre-existing idle source
guard. Even acknowledged writes leave it held. Multi-step workflows cannot run
continuously until 200b-c separately proves closure/admission. Tests pre-seed
independent phases to exercise each transition; they do not release guards
between transitions. Unknown/expired broker tickets keep calls charged and
active held, and archived collector jobs cannot reactivate. Nonce/body/principal
scope, fence, clock, counts, deadlines and bounded capacity use unchanged 199
business validation. Status and replay do not authorize network delivery.

Actual pinned 4.18.2 loopback OP_MSG tests exercise serialization and one-frame
391 source/commit errors. No Atlas requests or actual replica-set durability,
validator enforcement or crash persistence measurements are included. Gate 2
still requires the restricted no-creation role plus verified schema/index/DDL
boundary. Native 200b-c closure is the next separate review unit.
