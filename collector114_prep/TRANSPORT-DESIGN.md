# Next transport build (not installed, not saved)

Real HTTPS connector remains required. Build after113 review, preserving original
source feeds and source User-Agent. No live sources are called in offline tests.

1. Installation-owned hash-pinned source catalog, HTTPS443, exact selected URL.
2. A fixed-code child process owns DNS, socket, TLS and raw response streaming.
   Parent hard wall deadline kills/reaps child on blocked DNS/connect/read.
   Child environment cleared; memory/CPU/descriptors/output individually capped.
   Fetch child has network but never imports XML/full-text parsers or DB/mail.
3. Resolve bounded getaddrinfo set; reject the entire set if any nonpublic,
   translated, scoped, multicast, reserved or private address. Pin one validated
   address into socket.connect, check actual peer, retain original hostname as
   TLS SNI and validate chain + hostname via fixed approved trust store.
4. No proxies, no redirects, no retries within a single feed attempt. Standard
   library HTTP parser owns wire framing; reject duplicate CL, ambiguous TE/CL,
   unsupported TE, declared body over1MiB, and redirects. Read raw body in <=64KiB
   chunks, max1MiB, deadline updated per read; no response.content buffering.
5. Feed113 bounded decoder consumes those raw chunks. Both compressed and decoded
   budgets apply. Feed112 XML child stays networkless, separate from fetch child.
6. Structured bounded child output with URL + SHA256 + size, not raw exception
   strings or environment. Parent verifies all protocol values before parsing.
7. Offline fault tests: fake resolver, peer rebinding, TLS failure/SNI, redirects,
   CL/TE and chunked framing, read delays/never-return DNS, gzip bombs, output
   overflow, descriptor cleanup and parent kill/reap. No live effect tests until
   review and final cutover prep permission checks.

Deployment blockers remain independent of local success: Render process/resource
limits and bubblewrap support, interpreter/stdlib/trust-store pins, actual Mongo
roles/indexes/TTL, durable write reconciliation, service endpoint auth/idempotence,
Apps Script scheduler ownership and free-host capacity.
