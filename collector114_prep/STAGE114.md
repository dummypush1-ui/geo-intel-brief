# Collector114 fixed-code HTTPS connector candidate

INACTIVE. No app imports/mount, live fetch test, DB/mail/trigger changes. Not
live-ready or source-health verified. Installed feed allowlist only. Original UA.

Trusted fixed-code worker owns bounded DNS set -> all-answer public-unicast
policy -> pinned socket -> actual peer check -> verified hostname/SNI TLS ->
stdlib HTTP framing -> capped raw compressed reads -> bounded113 decode. No
proxy/env URL/redirect. Exact chunked without CL accepted; duplicates/TE+CL/
unsupported TE refused. UTF8 parser remains separately isolated112, not invoked
by this fetch worker. Requests compressed1MiB / decoded1MiB budget. HTTP header
framing is stdlib bounded at line/count level plus32/2KiB policy after begin.
Chunk extensions/trailers are bounded by worker CPU/memory and parent wall cap,
not claimed to have an explicit per-trailer budget. Need corpus/fault expansion.

Supervisor uses cleared environment, -I, separate session, whole timeout<=30s,
input<=128KiB/output<=2MiB, kill process group and reap. Fixed child CPU5s/memory
256MiB/file2MiB/descriptors64. Hash pins worker/connector/policy Python sources.
This is fixed-code resource containment, NOT OS sandboxing or confidential-file
containment. Child has network and read access; only trusted reviewed code runs.
Interpreter/stdlib/cert-store/site startup/compiled cache pins and deployment
paths remain gates. Parent worker protocol checks sizes/keys/address/hostname.
No request-supplied child commands, paths, socket/TLS factories or environments.

Local tests use mock DNS/socket/TLS and real stdlib HTTPResponse with supplied
BytesIO framing only. Supervisor faults run real subprocesses replacing the
fixed command in tests: hung resolver analogue, huge output, stderr and malformed
protocol. Local test results prove these offline mechanics, not live DNS/TLS or
Render behavior. Real live source health and Render process/isolation support
remain final deployment checks. Original gzip/encoding/header behavior parity
still needs source-specific verification, broader corpus and100-entry cap fix.

No durable DB writer/service/Apps Script trigger or production activation.
