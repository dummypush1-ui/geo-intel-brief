# Local Werkzeug fixture serving evidence

Test-only real loopback HTTP,127.0.0.1 ephemeral bound port0. No production
module or route change, DB, external source, credentials, mail, deploy or UI.
Python3.10.12 Flask3.0.3 Werkzeug3.0.6 PyMongo4.8.0 configured environment.

Four tests: complete response equals in-process expected CSV bytes, validator
parses one multiline row/footer/digest; no-store/fixture header; HEAD empty and
unauthorized403 start no export. Real TCP reset while producer awaits a known
pending data chunk and actual module slot is busy: socket SO_LINGER reset,
resume producer, closure occurs before completion and actual slot false; next
GET validates. Linux-only reset mechanics, no cross-platform reliability claim.

Slow-reader experiment is a CONTROLLED PRODUCER-GATE observation, not natural
socket backpressure or a measured timeout. Observed at least74payloadbytes received (headers separately consumed),
74producerbytes, producer unfinished, actualslot busy, socketdeadline2s,
forced reset/release cleanup. Gate is explicit and bounded4s. This does NOT
prove finite serving-slot lifetime, actual write timeout, natural slow-reader
behavior, Render ingress behavior or production deadlines. Those remain open.

Harness caps active request workers2, no daemon threads, bound server kept,
peraccepted socket timeout2s, absolute9s context budget; each event/socket wait uses minimum of local cap
and remaining deadline, bounded shutdown/joins,
server shutdown from test thread, workers joined before close, survivors fail.
Teardown release gate and close client sockets even if assertion/setup fails.
Worker exceptions collected; Werkzeug's normal disconnect handling is expected,
handle_error records every exception (including unexpected disconnect
exceptions), with fallback when exc_info is None; any recorded exception fails. Cleanup diagnostics do not mask an
original exception; they are printed alongside it. Actual module slot checked after teardown. Port is re-bound to verify release.
Real _pager and OriginalStream construction counters cover all requests;
unauthorized and HEAD assert0 before authenticated GET. HTTP/1.0 handler
pinned and close-delimited headers asserted. Client consumes the exact74byte
CSV header only, compares to expected full response prefix, and verifies
non-empty remaining expected bytes while producer held. Stalled producer is
NOT freed by client disconnect alone; releasing test gate is required.
No sleeps or header-case assertions. Server poll interval.01 is local lifecycle,
not website monitoring. These are local Werkzeug fixture evidence only.

Repeat evidence:200iterations/800test executions PASS with ResourceWarning
promoted to error. HTTP response EOF can precede request-worker completion;
harness joins completed request workers before issuing next request. Initial
repeat without this synchronization failed at113 due to cap2 overlap, corrected
and entire200 rerun. This is harness evidence only, not throughput readiness.

By-construction limits: expected CSV uses the same app implementation and thus
is not independent parity proof. Probe.remaining is set but not asserted;
actual client-prefix length and non-empty expected remainder are asserted.
Worker cap/start failure paths are implemented, not all fault-injected. Whole
fixture HTTP test suite needs full merged project/root assets for composition
exclusion tests. Extracted bundle executes serving tests only, not full app.
