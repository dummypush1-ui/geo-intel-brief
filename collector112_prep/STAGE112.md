# Collector112 supplied-byte parser preparation

SAFE independent review for inactive supplied-byte parser only. Production OFF.
Real feedparser6.0.11 over bounded supplied UTF-8 RSS/Atom inside bubblewrap.
Nine tests PASS with default Python and project3.10.12 venv. Vendored pinned
feedparser sources/sgmllib included, child PYTHONPATH=/app/vendor. Local reviewer
also observed distinct network/pid/mount/user namespaces, only loopback, child
PID2, cleared six-variable env, empty home/tmp/etc; resource limits CPU3s,
AS256MiB, file size1MiB, descriptors64. Fault output>1MiB and sleep20s killed/reaped;
NUL/UTF32/1001 entries refused. No unisolated fallback. Unavailable bwrap currently
propagates OSError, not ParserRefused (still no fallback).

These are LOCAL kernel checks, not Render capability. Read-only usr/interpreter/
app mounts expose broad readable code and are NOT confidential-file/arbitrary-code
containment. Pins cover Python source files only; interpreter/stdlib/site startup
and compiled-cache control remain final deployment gates. Vendored tree excludes
compiled caches at save; runtime controls are not established. Hostile corpus and
fault coverage must expand before live ingestion. Mount only intended artifacts
in final deployment; current installation-derived interpreter mount is a prep.

No client/index/TTL, live fetch, article write, mail, trigger installation, source
activation, production service mounting or cutover. Original feed date/selection
composition, network streaming/decompression/DNS, durable full-service integration,
source flags and article reconciliation remain pending. Original files unchanged.

Package test invocation from repo root: python -m unittest discover -s
collector112_prep -t . -p 'test_*.py' -v. Local default python3 and project venv pass.
