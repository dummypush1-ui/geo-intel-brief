# Injected Geo article writer: no activation

GeoArticleWriter maps only geo_intel/articles and accepts an injected client.
It never uses the read facade or creates a client, URI, index, route, scheduler,
mail, Telegram send or collector. Developer review requires the exact mapping,
write permission, verified unique URL index and source contract. This attestation
is self-declared, not owner permission. Real writes still need Push's approval.
The live client must be a reviewed PyMongo MongoClient with bounded connection,
socket and pool settings, suitable write concern and least-privilege credentials.
None of those live facts have been checked. This is not a hostile-client sandbox.

Input is the closed original post-fetch document contract. Caller IDs, emailed
and created_at overrides are rejected; Telegram ID must be null and URL empty.
The explicit fixed-zone clock supplies created_at in UTC. The writer takes a
bounded exact-built-in snapshot before validation: at most 1000 documents,
100000 visited nodes, depth 8, bounded fields and 2MB compact JSON. It rejects
summaries over 300 characters and scores outside [-2^53, 2^53]. The full batch
is validated before mapping or writing. Concurrent caller mutation is not an
atomic snapshot, but only the captured copy is validated and submitted.
Empty batches do nothing. insert_many(ordered=False) preserves the original
bulk path and missing emailed field. The driver gets its own list; attempted
count is captured separately so driver mutation cannot change reported totals.

Lookup and method binding failures cannot be classified as insert errors.
Only the insert invocation's BulkWriteError is classified. Receipt attributes
are read once; receipt exceptions are uncertain. Details access is redacted;
consumed receipt fields are captured as exact built-in values before parsing.
Confirmed counts require nInserted plus unique error indices to cover the whole
batch, no write concern errors, and final count coherence. URL duplicates need
code 11000 and exact integer keyPattern {'url': 1}. Other key failures are
failed, not URL duplicates. All non-URL failures still use state 'partial'.
SON document_class or double-valued keyPattern yields uncertain; pre-4.2 servers
missing keyPattern yield failed. This intentionally prefers uncertainty to a
false duplicate claim.

Network, malformed, unacknowledged or write concern outcomes are uncertain:
inserted/duplicate/failed counts are None. Writes may already have happened.
No retries, raw error text or IDs are returned. Partial/uncertain outcomes need
source reconciliation under a separate grant; recovery is not implemented.
Original BulkWriteError's loose len-minus-errors estimate is not reused.

Tests: 22 focused tests with native PyMongo 4.8.0 passed locally and from the
extracted bundle. Independent v4 review passed 20 tests with PyMongo 4.18.2;
the final two bounded-input checks were reviewed by own tests and sanity diff.
Repro: python -m unittest tests.test_geo_article_writer -v. Dependencies:
python-dateutil 2.9.0.post0, PyMongo 4.8.0, Flask 3.0.3, Werkzeug 3.0.6, PyYAML 6.0.2.
Tests use fake driver clients only, never a real database. No durable stream or
account store is wired by this increment.
