# Before implementing autonomous recovery or live execution

A durable ledger is necessary but NOT sufficient. A fence value stored in
Mongo cannot prevent an old process inserting articles after losing its lease.
No write-capable automatic reclaimer will be implemented by pretending a
find_one lease check is atomic with a separate insert_many.

Safe possibilities for review:
- Single Mongo transaction includes ledger claim/version assertion and exact
  article inserts; transaction timeout/row/size bound, driver-supported replica
  topology. Must validate actual capability and role before relying on it.
- Keep expired active profile latched; prove old process stopped/reap or owner
  pauses old/new entrypoints, reconcile per-run expectedURL/hash receipts,
  then separately authorize unlock. Lower availability but no doublewriter.

Request-driven recovery must use immutable bounded candidate checkpoint before
write_started, run-specific outcome record, durable terminal acknowledgement,
source/fingerprint drift refusal. Any article readback requires reviewed role;
current readOnly/public latest100 is NOT a write-reconciliation oracle.
CheckpointDB role/mapping retention/disclosure is not granted by freechoice.

Upcoming bounded composition can be tested against fixed supplied entries with
original post-fetch semantics and injected in-memory outcomes. It must carry
explicit no-network/no-livewrite labels. Arbitrary external XML/fulltext needs
resource-isolated parsers and verified packages; no import legacycollect() as
shortcut (creates stores/Telegram daemon/network environment sideeffects).
