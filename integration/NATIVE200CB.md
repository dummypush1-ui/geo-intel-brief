# 200c-b read-only measurement harness: observed evidence only

integration/native200_readonly_measurement.py is a DEFAULT-OFF observation
function. measure(client, enabled=True, fingerprint=...) requires an explicit
owner-constructed pinned PyMongo 4.18.2 synchronous client, the reviewed
collector fingerprint and a monotonic clock. It NEVER constructs or closes a
client, starts a session/transaction, reads a URI/environment, installs a
schema or runs any write command. The command allowlist is exactly: hello,
buildInfo, listCollections, listIndexes, find and majority count on the fixed
eight geo_intel collections, every one with maxTimeMS 2000, exhausted
single-batch cursors (no getMore) and the 8 MiB command/reply cap.

## What one successful run establishes

- Observed replica-set primary topology (not a URI assertion; mongos and load
  balanced service IDs refused), sanitized server version string and pinned
  driver hash verification.
- All eight collections exist as ordinary collections with exact typed
  strict/error validators matching the reviewed VALIDATORS set. Comparison is
  Canonical Extended JSON with sorted keys, so an int/long bound stored as a
  double, precision loss or width drift is a STOP, never a silent pass.
- Ordinary unique _id index, no TTL index, bounded index inventory.
- Complete bounded contents: every document, string identities unique,
  per-collection 16384-row cap, cross-checked by a majority count so a
  silently truncated singleBatch is a STOP, total observation byte cap 32 MiB.
- Complete immutable archive chains for both families revalidated offline by
  the reviewed 199 verifier: manifest linkage, record hashes, chronology,
  fence/revision consistency, no archive orphan or missing row, retained
  collector checkpoints subset of known jobs and equal to archived copies.
- Journal consistency: exactly two guards, serial/contiguity, plan shapes,
  outcome markers canonically equal, admission closure linkage to proven
  source hashes, acknowledged operations proven against current source
  revision and after_hash.
- A second full inventory after validation; ANY data/schema/index change
  between the two reads is a STOP, because this is NOT an atomic snapshot.

## What a PASS is NOT

ready stays false. A run is observed evidence at two read instants, not an
atomic snapshot, not proof of quiet writers, not crash/commit durability, not
live-readiness, not role/privilege verification, not capacity release and not
retry/recovery permission. No measurement here turns collectors on, proves a
real Atlas cluster correct or authorizes the next gate.

## What is deliberately absent

No dormant mutation tests, no drop/recreate probes, no transaction body
maxTimeMS measurement, no 3 GiB workload, no write harness hidden behind a
flag. Those exist only as future separately reviewed scopes with
owner-approved disposable mappings; the fixed geo_intel stores are never
repointed at an invented staging DB. On ANY refusal the harness stops with no
mutation, retry or repair; reauthentication (391) is consumed and re-raised,
never replayed.

## Output evidence

Sanitized hashes per collection (validator/index/data SHA-256, row counts),
chain summaries, guard phases, observed byte total, driver and sanitized
server version. No host names, credentials, URIs or document contents are
returned. Evidence is for owner/reviewer comparison against the approved
200c-a package; it grants no permission by itself.
