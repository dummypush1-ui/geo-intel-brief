# Collector113 transport policy and feed composition preparation

Inactive supplied-response tests only. Production OFF. Public repository backup,
not the finished app. No real HTTP/DNS/TLS, no DB/mail/trigger/runtime changes.

New policy checks installed exact feed URLs, public-unicast supplied DNS answers,
supplied peer membership, explicit deprecated192.88.99.0/24 deny, HTTPS443, no fragments/redirects. Keeps hostname for
future TLS SNI/certificate checking. Supplied raw wire chunks capped at 64KiB per
chunk, 4096 chunks, 1MiB compressed and 1MiB decoded. Supports identity, gzip and
zlib-wrapped deflate only; rejects excess/truncated/concatenated compressed data,
length mismatches, duplicate headers and ambiguous transfer framing. Deadlines
checked before/after each supplied chunk. Hostile gzip expands only to remaining
output budget plus one byte.

Feeds: hash-pinned original DEFAULT_FEEDS AST literal (25 sources); no original
module imports. A supplied response passes through these policy checks, then the
reviewed112 OS-isolated feedparser, then the original hash-pinned feed-selection
AST composition. Title/link, summary cleanup, cutoff, fixed-date fallback and
source/credibility behavior tested. Bozo and parser projection counts retained;
no claim that a malformed parsed source is healthy. Original112 projection is
100 entries, MAX_ITEMS selection bounded to100; full original larger settings
remain a parity gate. Originals and prior preparations unchanged.

17 offline tests pass in the project Python3.10 environment. Supplied address
checks are not live DNS resolution, connector pinning, TLS verification, or peer
inspection. This stage deliberately has no network connector. It cannot interrupt
a blocked resolver or socket reader. Real raw streaming, HTTP framing, DNS/connect/
read deadlines, connector address pinning, actual peer/TLS checks, gzip/encoding
parity, broad hostile corpus and Render bubblewrap/runtime mounts remain gates.
No confidential-file containment claim. No live source health proof.

Invocation: python -m unittest discover -s collector113_prep -t . -v
