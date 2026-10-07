# Collector109 stage1 revision 2: INACTIVE, offline only

No live entrypoint import, network call, Mongo client, trigger install, repo save,
or cutover. Uses saved collector108 and hash-pinned original source contracts.

Changes responding to NEEDS-CHANGES:
- HIGH1: existing write_started is never replayed. Only the invocation winning
  the prepare_complete -> write_started CAS may call the writer. A second
  heartbeat checks current ownership/lease just before that call. Crash or
  uncertainty requires reconciliation; there is no automatic lease steal.
- HIGH2 (receipt): exact writer schema/state/type/bounds/accounting validation.
  Missing, malformed, unknown or explicit uncertain receipt latches uncertainty.
  If lease/store prevents terminal update, write_started stays locked and the
  result says reconciliation_required. No guessed zero counts or completion.
- HIGH3 (encoding): tagged typed canonical encoding separates literal containers
  from datetime/scalars; rejects nonfinite floats and non-string dictionary keys.
  Existing equal-hash put does not replace a checkpoint row.
- HIGH4: driver requires an immutable FULL run checkpoint: candidates, active
  categories, threshold, key and fence. Every resume must match it before prep.
  Missing/mismatched checkpoint refuses. Uses bound copies, not caller values.
- LOW: no author /tmp import paths. Root PYTHONPATH is a test-runner input only.
  Package imports are validated from a separately copied root. Preparation
  exceptions fail_before_write when ledger authority is valid; if that update
  cannot be verified, refusal instructs checking ledger status. No article write.

32 focused offline tests pass. Safety tests cover wrong/expired write_started,
two resumed drivers (zero new writer calls), crash immediately after ticket,
concurrent prepare drivers (one total writer call), clock expiry before writer,
malformed receipts, typed collisions, run settings replacement and prep failure.
BoundedFetcher is an injected transport contract, not a live RSS implementation;
its six initial URL-host errors are fixed. No content-type/parser claim is made.

Important limits:
- FixtureCheckpoints is in-memory. Process-restart recovery is NOT implemented.
- Fencing the job ledger cannot fence an external article database operation.
  Production remains OFF until transaction/reconciled article writes and durable
  checkpoint/ledger stores with majority+journal are independently verified.
- RSS parser sandbox, real network streaming/decompression budget, DNS/IP policy,
  fulltext/GNews/Telegram backup flags and actual deployed triggers are pending.
- Endpoint/Apps Script drive wiring is next, outside this stage1 review bundle.
- Live switch, DB/mail changes and stopping old collectors need explicit owner OK.

Final package runner: python -m unittest discover -s collector109_prep -t . -p 'test_*.py' -v
Independent review: SAFE for inactive fixture/preparation scope. Candidate count
1000 does not establish aggregate byte/depth/time bounds. Production stays OFF.
