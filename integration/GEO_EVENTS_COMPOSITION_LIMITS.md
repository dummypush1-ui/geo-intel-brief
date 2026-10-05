# Separately gated Geo events and original digest read composition

NEWS_EVENTS_READ_ENABLED=false default. True requires NEWS_READ_ENABLED=true,
private preview access and NEWS_EVENTS_MAPPING_VERIFIED=true before client.
Exact geo_intel/events only; no override inferred from article mapping. Explicit
GEO_EVENTS_ALLOWED_HOSTS comma-separated public hosts, no whitespace/duplicates,
max20 hosts/2048chars. Host catalog is display link safety, NOT source ownership,
credential read authority or policy approval. Dedicated read-only Atlas user
must separately cover exact events collection. No real credential verified.

Uses the SAME gated narrow Geo client, not BRICS/client2. No writes/commands/
aggregate/indexes. Existing article reader unaffected, events off maps none.
ReadOnlyEventsReader preserves inclusive UTCtoday..today+90day query, ascending
event_date, projection with _id excluded,1001row overflow guard/1000cap,2MB
snapshot/16kfields/query2s/cursorclose. DashboardSnapshots filters display
labels/links then caps100; digest additionally applies its90day window.

Only original digest includes events, matching existing report behavior.
Critical and weekly report paths don't read events; no invented new block.
Hash-pinned source renderer loads AST definitions only, no original config/DB
imports/SMTP functions. Existing reports remain bounded supplied article samples,
not current unsent queue/full-history weekly statistics. No mail/mark/scheduler.

Events failure becomes unavailable panel, not supplied_snapshot with zeroitems.
Article reads remain available if events fail. No automatic polling/retry loop;
manual request may attempt source again. Shared client lifetime remains article
failure close-once/latch; event failure cursor closes but doesn't close client.
Unavailable metadata is visible even when original HTML omits event section.
No live source read/deploy/environment change by this increment.

4 focused composition tests PASS in rebuilt configured environment. Finder
index seam mocked as synthetic context, NOT original Finder parity proof.
Pinned original renderer source restored from backed repository and hashchecks
run in test. Tests private403/gates before constructor/exact query projection
sort/limit/maxtime/close/originaleventblock/errorunavailable+articlesstill200.
Review bundle includes integration dependency tree, test helper and three
original report sources. Installed Flask/PyMongo/PyYAML required, no rootFinder
assets needed for these4tests. No hosted proxy/schema/index/permissions proof.

Real events documents not checked. BSON datetime event_date or numeric confidence
won't satisfy bounded string reader contract, may show unavailable until real
one-time source check. Both events+articles must be independently covered by
read-only Atlas role. Punycode display hosts rejected by existing public_host.
Add short bounded cache before wider exposure; current per-request opt-in path
has no cache, polling or background retries. Fresh independent review SAFE,
4/4PASS reported; no real-document validation inferred from fixtures.
