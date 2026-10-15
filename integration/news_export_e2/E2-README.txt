E2: original-column Geo snapshot CSV HTTP bridge
Baseline:761f8f5657187f994f200db23c78dc55770f607c
Default OFF, local candidate. No deployment or proof of live source review.

Scope
- New GET/HEAD /api/geo-original-export.csv. Existing latest100 CSV and the
  generic export-full route are untouched; no fallback between them.
- The live public builder can accept geo_export_binding=SourceBinding(...).
  The sample builder refuses activation. No default production binding/provider
  is installed. This unit is a builder/HTTP connection, not turnkey live export.
- Flag PUBLIC_GEO_ORIGINAL_EXPORT_ENABLED must be exactlytrue, with public live
  reads and their mapping/disclosure/read-only gates. OFF accepts no binding,
  reads no pins and creates no source client/session. OFF response parity is
  tested against frozen baseline builders. No old route or UI changes.
- SourceBinding is an explicit trusted application input, not proof of review.
  Its exact original GEO_FIELDS public-disclosure declaration is separate from
  the existing normalized public-news fields. Original fields include country,
  corroboration, published and created_at; ObjectId and unknown fields are not
  exported. The caller owns its raw client; this module never closes it.
- Existing create_geo_original_stream owns a per-request snapshot session with
  exact geo_intel.articles mapping, binary collation, pinned original score DESC,
  published DESC, ObjectId DESC order, and a reviewed named index. It scans ALL
  sort keys in that snapshot before emitting any CSV, rejecting unsupported
  schema rather than silently losing old records. This can be expensive.

CSV contract and honest bounds
- Original Geo columns, original category semantics and cap-before-filter order.
  This is not a CSV of current browser search results. q/country/project/sort and
  repeated/unknown query names are rejected; only original category is allowed.
- Existing streamer enforces at most1,000,000 input rows,20MiB output,120seconds
  checked during production, bounded500-row pages and2MiB materialized pages.
  The final fixed-width CSV row says EXPORT_COMPLETE, EXPORT_TRUNCATED or
  EXPORT_INCOMPLETE and gives rows, source-read count, content-cell truncation
  flag, reason and SHA256 of preceding CSV bytes. HTTP200 alone is NOT success.
- Formula defenses,8k exported-cell cap and reserved EXPORT_ cell escaping are
  preserved. An interrupted download missing its final status is incomplete.
- HEAD validates arguments and returns metadata only, without source/session,
  slot or snapshot checks. It does NOT prove readiness. It can return200 while
  source GET would fail or another export is busy.

Resource and failure ownership
- A process-wide single export slot is shared by separately built apps. This is
  NOT a distributed quota across workers/instances and not protection against
  hostile public traffic. Existing public/edge request guards still matter.
- Wrong host and non-GET/HEAD refused. No method overrides. No conditional/range
  partial success. no-store, no-referrer, nosniff, deny CSP on endpoint responses.
- First-page/preflight failure returns generic503 and releases session/slot.
  Later source failure emits EXPORT_INCOMPLETE. Disconnect/iterable.close(),
  unstarted close, shutdown, start_response failure and replacement error response
  after an after_request failure all clean up exactly once. Cleanup never closes
  the caller's raw client. No retry or background export/cache is started.
- Production-time120s is cooperative, not a watchdog for a client that stops
  reading. A stalled WSGI consumer holds the slot until the server closes it or
  worker exits. Deployment needs reviewed worker count, socket/write deadlines,
  proxy buffering and disconnect behavior. No global memory/rate guarantee.

Validation
- tests/test_news_export_e2.py exercises the real snapshot/stream code with fake
  Mongo sessions/cursors:501rows across pages, original schema, category filtering,
  final digest, no unknown-field leakage, no startup/HEAD source effects, admission,
  abort/unstarted/start_response/after_request failure, late failure and shutdown.
- Existing GeoSnapshot, OriginalStream, RawPager and original serializer tests
  remain separate. No real Mongo/provider/production reads were made.
- Source pins bind six unchanged export modules. Derived inventories reflect
  the real parent761f8f5. No new third-party package is introduced.

Remaining activation gates
1. Independently verify the live raw source credential is read-only, actual full
   schema/order coverage, snapshot support, binary index/explain and all original
   export fields' public disclosure authority. Binding booleans alone prove none.
2. Supply that binding through an explicitly reviewed production composition;
   do not unwrap the ordinary read facade or infer a client from an environment
   URI. The read facade intentionally has no snapshot/session/hint API.
3. Review actual server capacity, timeouts, transport/disconnect behavior and
   response trailers before enabling. Add a clearly labeled UI download only as
   a separate reviewed unit; current search-result export is not implemented here.
4. Independent code review, owner approval for each push, separate cutover.

This closes a bounded code seam. It does not complete all old-news search/export,
BRICS export, raw archive export, AI, tariffs, collection or mail.
