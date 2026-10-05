# Geo original CSV snapshot adapter (offline injection, not live wiring)

create_geo_original_stream requires injected driver client plus closed explicit
review of geo_intel/articles/read-only role/snapshot support/index name/explain.
No URI/client construction, environment/router selection, read61facade expansion,
aggregate/command/write/index creation or source probes. Callback attestations
are developer prerequisites, NOT independently established real-source proof.

Starts PyMongo snapshot=True,causal_consistency=False session. Complete ordered
projection scan validates every score/published/ObjectId with existing resume
contract before header. It rejects mixed/missing/null/unsupported keys anywhere,
not filtered typed sample. Same session/simple binary collation/exact named hint
for schema scan and all original keyset continuation pages. No count/aggregate
added. SnapshotTooOld/indexmissing/unsupportedserver errors fail redacted; no
retry or fallback to inconsistent reads. Full preflight can be expensive and
must finish inside sampled120s budget; may refuse large history, notmillionrow
throughput claim. Sort ties _idDESC added by existing reviewed keyset contract.

Query max_time_ms2000, batch100, page500 (adapter rejects>1000),2MB retainedpage
budget, bounded fields before copy. Provider BSON allocation/buffer happens
before Python checks; upstream injected client MUST have reviewed socket/connect
and pool bounds. No synthetic guarantee of interrupting blockedcalls. Current
stream20MB/1m cap/8kcell clipping and explicittrailer unchanged. Sampled remaining
stream budget is inside snapshot120s total, external slowclient timeout still
required beforeHTTP exposure. Request filters stay AFTER cap, no querypushdown.

Managed wrapper owns session end once alongside exact OriginalStream cleanup:
initialfailure, latefailure, EOF, explicitclose, neveriterated close, context.
Caller still MUSTclose disposed response; no destructor/GC/watchdog guarantee.
Preflight and page cursor closes before end_session on failure. Client externally
owned and never closed by adapter. No real DB accessed; no index/server/user
credential/schema/collation/explain attestation validated here. Geo only, no
BRICS migration. Original fixtureHTTP is untouched; no new route or UI exposure.

Repro: pip install pymongo==4.8.0 Flask==3.0.3 Werkzeug==3.0.6 PyYAML==6.0.2;
python -m unittest tests.test_geo_snapshot -v. Bundle contains integration tree
and tests; no original Finder/root assets required.10focusedfake-driver tests:
reviewbeforeeffects/snapshotflags/samesession/full501multipage/querycontinuation/
completefullschema/orderrefusal/deadline/pagebytes/earlylateerrors/closeidempotent.

Driver docs inspected for snapshot semantics:
https://pymongo.readthedocs.io/en/latest/api/pymongo/client_session.html
https://www.mongodb.com/docs/manual/reference/read-concern-snapshot
MongoDB5.0+ snapshot reads required; source operator still must verify actual
server support and independent credential/index permissions before activation.

V2 query boundary: adapter owns last continuation; complete supplied plan must
match query_plan for that typed resume/limit. Extra operators ($where included),
malformed $or or injected predicates rejected before find. Schema/page/factory
errors raised after exception scope, no __context__ source error retained.
12focused tests (v2) include query injection and context retention regression.

max_time_ms applies initial find, not a finite deadline for every getMore;
client socketTimeoutMS and serving cleanup remain required. Attestation is
self-declared, not independently measured. Full schema preflight scales with
collection size and may exceed budget. MongoDB5.0+ required, AtlasM0 snapshot
support has not been verified. No live availability implied.

V3 initial guards moved into cleanup/redaction scope: exact plain plan,
missing/None/wrong project and malformed scope close session once, no unredacted
AttributeError.14focusedtests include execute/scope malformed-entry regressions.

Reviewv3SAFE14/14. Constructor review values are trusted developer injection,
not untrusted input sandbox: an object with raising equality can expose its
exception before session. Control exceptions during adapter calls are converted
to redacted SnapshotUnavailable after cleanup (not preserved cancellation).
