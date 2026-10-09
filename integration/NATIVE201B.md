# Native 201b: unselected broker, collector and composition

New native201_broker accepts only AdmissionProxyReceiptBudget and the existing
exact FixedProxyTransport. Auth/session/CSRF/principal scope and closed ships/AI
routes remain mandatory. Only known claim AND send-start ACKs allow proxy entry.
Replays return status only, not cached answers. Unknown/late transport holds the
global ticket; no refund, resend or upstream-stopped claim. Existing empty model
catalog stays closed, provider restrictions unchanged. No actual proxy call in
fixtures: transport execution is mocked.

New native201_collector accepts only NativeCheckpointCollectorLedger and
NativeCoverageCheckpoints on the same client. Existing CollectorConfig, supervised
whole-cycle fetch contract, resource evidence and exact GeoArticleWriter guards
remain. After fetch and heartbeat, checkpoint_and_advance atomically inserts the
immutable checkpoint and advances running -> fetch_complete with its marker.
No ordinary checkpoint put/upsert. All later ledger steps use native admission
and journaled source mutations. Replays never fetch or enter article writes.
Article writes happen only after known write-started ACK and heartbeat/evidence.
They are NOT claimed transactional with ledger/checkpoint operations.

New build_native_composition default OFF returns the public app unchanged.
Explicitly enabled source fixture mounts the same closed authenticated broker
routes and owner-Bearer retained collector GET-status route. Collector auth,
Origin/query/body/method/key checks precede state access. Status requires current
job evidence and exact retained checkpoint/hash coverage; generic 503 on missing
or corrupt state, never recovery permission. Responses are no-store.

Existing 199 gates/source, production_entry.py, public_live107.py, collector197_job
and orchestrator remain unchanged and reject the new types. No env/client creation,
production selection, migration, timer, workflow edit, live flag or DB provisioning.
Default-off/source-only/unselected. Production factory is a later 201c unit after
gate2/3 contracts align; owner final live approval still required.

Pinned4.18.2 loopback lifecycle tests prove serialization and local behavior,
not Mongo validation, isolation, replication or crash durability. Gate2 least-
privilege role is NOT creation-proof: INSERT can create collections. Owner-only
exclusive DDL boundary plus all8exact schema inspections and accepted ONE-write
TOCTOU effect (then next inspection holds) remain requirements. Real staging
normalization/$or/oneOf/BSON/maxTimeMS and diagnostic evidence are unverified.
