F7: complete held source-to-artifact chain, not runtime binding or deployment

Default OFF MERGED_FINDER_CHAIN_PREP_ENABLED=false. Requires all7preparation
flags exactly true before any source acquisition or build. Exact upstream40hex
commit only. No branch head selection, scheduler, retry, provider or credential.
F3 performs its fixed5bounded unauthenticated Git commit/root-tree/src-tree/raw
reads, checks exact regular blob modes/size/Git SHA1 and source SHA256. No source
app/updater code is imported/evaluated. F2 still closed-data parses2files, keeps
all previous partner values and sanctions rows, adds only newly seen codes and
rows in held scratch. Its new plan() returns the same candidate and delta data
without building. Existing prepare() wraps plan() and ordinary F1 report build,
with unchanged disabled/report behavior covered by existing tests.

F1 adds explicit prepare_package() wrapping its same checked scratch build,
syntax validation and changed-output/consumer report. Before temporary cleanup,
fixed F6 receives actual generated4pins and transformed2source pins and returns
the full held bytes. No arbitrary callback or user-controlled code path. The
ordinary prepare() path remains report-only and deletes scratch as before.
F7 adds exact original public upstream2source bytes and one canonical receipt
containing F3evidence, F2held deltas, and F1rebuild report. It rebuilds the closed
ZIP and manifest in memory, using F6's actual-byte/name/CRC/hash verification.
Provenance JSON cap2MiB; F6's16payload/140MiB raw/40MiB compressed caps remain.

Real current local baseline9902d202, original commit9133270856bb77170956b707bafe260997690d80:
5requests/3903510bytes, zero credentials/redirects/retries/provider calls;
partners42->63 (+21), sanctions75163->75166 (+3),202missing retained,0removals.
Scratch data.aa056ad4e0cf.js. Complete15entryZIP34457604bytes,
SHA2564648c42574d6e158198ac4f812c8648ce3af6b2f50bdee8f2fbb33236bb01c90.
Both exact upstream files, transformed files, completegeneratedbytes, index,
rows, binary identityproof and safe review render are inspectable together.
Report state held_complete_source_chain_not_runtime_rebound. No caller output
file is saved, no publication/auto-repin, no original tree writes. Scratch
writes/deletion are existing isolated build mechanics, not production writes.
Source labels retain F3's between-response90s budget limitation; not a watchdog
that kills an ongoing continuously slow response. Official source freshness,
legal screening, changed partner values, sanctions removals and AI/GST
semantics remain unapproved/unverified, not inferred from original repo data.

Remaining: independent review and complete byte transfer; explicit atomic18
consumer edition/pin/source binding; last-good active-source/scheduler/status;
separately authorized public deployment and cutover. This unit closes the
source-to-held-review-artifact chain only, not full original/live Finder parity.

Review clarifications: F2prepare() returns semantically equal data but its JSON
key insertion order changed: rebuild is now last. Consumers must not depend on
that key order. fetch/clock/root are in-process test seams, never HTTP parameters
or caller authority. Defaults use the fixed F3 fetcher and repository root.
Complete packaging holds about125MB of raw bytes plus compressed ZIPs/repack,
index derivation and runtime overhead. Run off Render only in an offline review
worker with enough memory; do not enable this operation in the web process.
F7 repacks only F6manifest-declared payload names. An undeclared extra ZIP member
is not propagated. The direct ordinary chain receives F6's just-verified bytes;
this behavior is not a general untrusted external archive acceptance API.
