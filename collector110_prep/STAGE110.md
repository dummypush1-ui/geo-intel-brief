# Collector110 input-budget and checkpoint-store preparation

INACTIVE scratch only, unreviewed. No production/import/client/index/TTL/env
wiring, repo save, database access, trigger, mail or cutover effect.

input_budget.capture bounds input BEFORE expensive copying/hashing/preparation:
2MiB conservative UTF-8 content, 20000 nodes, depth8, 100 dict keys, 1000 list
items, bounded strings/signed-int64 integers, exact builtins and reviewed timezone dates.
Cycles/nonfinite/scalar subclasses/custom objects fail. Shared subtrees count
again. This is not a measured CPU deadline or BSON byte bound; it is not yet
wired into saved109, so does not improve109's current input guarantees.

DurableCheckpoints accepts an injected collection only, validates configured
write majority+journal+wtimeout and read majority concerns, creates no client or
index, and uses _id immutability with setOnInsert + readback/hash verification.
Typed JSON/BSON-compatible projection retains dates without driver normalization.
Missing/malformed/unacknowledged/mismatched writes/readbacks refuse. All tests
use an in-memory collection double; NO real Mongo/server validation occurred.
Concerns on a Python collection do not prove server capability or owner authority.

21 focused offline tests PASS, including second-adapter retention, immutable
mismatch, corruption, concern validation, uncertain receipt, readback failure,
parallel different inputs (one winner), encoded-depth/cycle/resource rejection.
Not attached to109 driver (that explicitly accepts FixtureCheckpoints only).
No claim of production recovery, live storage, lease takeover or article fencing.
Next increment after review must separately wire this boundary, validate actual
role/server topology and use resource-isolated network/parser work. Article
write_started remains latched pending reconciliation; no retry/unlock added.

Revision2: integer capture uses signed-int64 range. Wire input integers are
canonical decimal strings with strict decoding, avoiding PyMongo Int64 subclass
changes on BSON roundtrip. Stored fence is also decimal text for stable identity.
Real BSON codec roundtrips at both signed-int64 boundaries PASS; one-beyond
values refuse before collection access; malformed decimal encodings refuse.
These are local codec tests, not a live Mongo write/capability test.
