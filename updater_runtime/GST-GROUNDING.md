GST proposal evidence, item21

A proposal is not a rate decision. Match one table row with an explicit 4/6/8-digit code, exactly one rate, and exact description. Two-digit chapter matches,
code substrings, rates on neighboring rows, multiple matching rows/rates and
scope modifiers, exemptions or footnotes are held. Structured evidence carries
line, row, code, rate, description, nearby context, scope and review_required.
Conservative matching can hold legitimate wrapped tables; manual review is the
intended path, not a silent fallback. No claim that nearby context proves the
notification's complete legal effect.

All new proposal files have state=manual_review_required. apply-gst refuses
that state. An operator checks the full official notification, strips evidence
fields to the existing reviewed schema and sets state=operator_reviewed before local
PR preparation. There is no production approval endpoint or automatic rate
commit. Held candidates retain their reason/source in the proposal artifact.

PDF extraction requires declared Poppler pdftotext 22.02.0, checked exactly at
runtime (binary version, not an attested package hash). Missing/drifted tool,
invalid/oversized PDF, extraction error, timeout, empty or oversized text fail
before seen-state updates. Each extraction uses a private temporary directory,
spawn without a shell, and cleanup. Deployment must install/verify this pinned
input separately; these changes install nothing and activate nothing.
Bounded streamed PDF reads cap 10 MiB, output 2 MiB and extraction 20 seconds. Test
fixtures may supply arrayBuffer only; size is checked before extraction.

Pending proposal sources are merged without replacing existing source evidence.
A held-only later run cannot wipe prior changes. Completed/reviewed files must
be archived by the operator before the next proposal batch. PDF failure blocks
the batch and retains seen-state; the updater log identifies the held notice.
Poppler has time/output limits, not an OS memory limit. Deployment must add
process isolation/memory limits before treating hostile PDFs as production-safe.
