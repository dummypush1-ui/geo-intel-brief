# Native 200b-a: source only, default OFF

Adds a new NativeArchiveCore and fixed raw bridge. No existing 199 types,
adapters or gates change, and existing exact type gates reject the new core.
No production selection, client construction, env reading, migration, mail,
Atlas operation, workflow file or deployment is included.

Eight exact geo_intel collection mappings are inspected with listCollections
and listIndexes before enabled core use and before writes. Collections must
already exist, journal validators must exactly match VALIDATORS (strict/error),
and every collection must have an ordinary unique _id index and no TTL.
Inspection is read-only and bounded to exhausted cursors. No getMore/provision.
Observed inspection cannot prevent an owner concurrently dropping a collection.
Gate 2 therefore additionally requires a verified restricted role without
collection-creation privilege, verified schemas/indexes, and a maintenance
boundary for owner DDL. This code does not grant or configure those permissions.

Outside-transaction finds use majority readConcern; writes use majority+journal
with a 5-second write-concern timeout. Native transactions inherit the 200a
snapshot/majority settings. Every bridge operation uses one checked-out primary
connection and command(no_reauth=True), never Collection retry wrappers.
Commands have 2-second maxTimeMS and an 8-MiB encoded command/reply cap. Finds
request at most two rows, reject duplicates and nonzero cursors. Index inspection
is capped to 16 rows. This pins the existing 4.18.2 private-driver source surface.

Guard CAS is first, then majority readback, then immutable intent insert and
readback, all before the write transaction begins. The core independently plans
under a read-only transaction, reserves the journal, and revalidates the full
bounded chain and source revision in a fresh native transaction. Source CAS and
outcome marker are in that same transaction. commit_attempt is durably recorded
before the sole commit primitive; acknowledged is recorded after its ACK.
Failure/unknown outcomes remain held. No retry, reclaim, TTL, deletion, release,
or rollback compensation is provided. Even an ACKNOWLEDGED operation retains
its guard. Restart reconciliation only reports observed facts, never permission
to retry or clear holds. A missing intent after reservation is a hold.

One guard per source limits this unit to one successful operation until a
separately reviewed closure protocol. Serial capacity is 4096 and is never reset.
The new native collector ledger/budget adapters are a separate 200b-b unit.
Continuous cadence, actual replica-set durability, real 3-GiB measurements and
live cutover are not proved or authorized by these fixtures.

Tests use the actual pinned PyMongo driver against a synthetic loopback TCP
OP_MSG server, including kind-1 document sequences. This exercises real driver
serialization/no-reauth behavior, not MongoDB isolation, validators, replication,
crash persistence or transaction durability. Synthetic crash cuts are simulated
lost/error replies after processing, not operating-system power loss.

## Superseded gate2 role claim

The earlier no-creation-role requirement above is superseded by
NATIVE201GUARD.md: INSERT itself can permit implicit collection creation.
The operational role is least-privilege, NOT creation-proof. All-eight exact
validator preflight, owner-exclusive DDL boundary and an accepted one-write
inspection/insert TOCTOU effect replace that claim. No zero-effect guarantee.
