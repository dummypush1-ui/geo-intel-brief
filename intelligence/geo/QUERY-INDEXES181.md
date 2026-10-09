# Source query-index proposals

connect() is locked for lazy initialization. MongoClient and database are built
locally and published together. Failed database selection closes the new client
and leaves both globals unset. Clients are shared per process, not per thread.
No connection, URI, live database or indexes were inspected by this change.

init_db() retains its existing four index calls. New compound candidates require
explicit provision_query_indexes=True; no production caller sets this flag.
This source-only gate is NOT permission to create Atlas indexes. The caller must
review current schema, names, duplicate keys, collation, storage costs and explain
plans separately before provisioning. No TTL or deletion indexes are added.

Candidates match existing queries, without changing filters or result order:
- score/published/_id/emailed: dashboard score order and unsent queue sort.
  emailed $ne true also includes missing fields; it is NOT an equality prefix.
  Filtering follows sort keys; this does not promise a cheap or covered query.
- published/_id: newest order; title/_id: title order.
- created_at: latest collection, retention review and date aggregates/ranges.
- risk_level/score/created_at: critical equality, score order, date range.
- score/created_at: weekly score order and date range.

Sort-first ESR tradeoffs can scan many rows when date ranges are selective.
Live explain evidence may choose a different range-first index. Existing URL
unique, score-only and event-name/date/date indexes remain; no indexes are dropped.
Default callers remain without the six extra provisioning calls. This closes the
source init race/proposal gap, not live index provisioning or performance proof.
