# Collector109 wiring preparation: INACTIVE fixture only

Stage1 revision2 and this wiring increment have SAFE verdicts for inactive fixture/preparation scope only. No production approval.
Not mounted in production. No repo save, network calls, triggers, live DB/mail
changes or old-service stopping. collection_only.gs is an additive 108 test companion (including the earlier
phase type check), not a replacement for old108 or Code.gs.
The new drive app does not expose 108 submission or health routes. The
keepAlive/submission-to-drive chain is not mounted as one complete service.

- FixtureService registry accepts full run inputs only through offline explicit
  server setup. HTTP caller cannot submit candidates/categories/fence/writer.
- Auth precedes parse/ledger access. POST /internal/collector109/jobs/<key>/drive
  accepts only an empty JSON object and invokes hold-only drive (no writer/store).
- GET status returns sanitized ledger job/phase/counts.
- Apps Script polling reads preserved COLLECTION_PENDING108; derives key from
  nonce; validates status binding/counts; skips terminal/write_started/uncertain
  jobs; drives only before write and validates hold + authoritative status.
- Never clears pending or generates a new nonce. No background threads and no
  automatic recovery. The process-local input registry blocks after restart.

Six Python endpoint fixture tests + Node script assertions pass.
This is wiring preparation, NOT a working production collector. The real input
fetch/parser/checkpoint registry and production article writes remain OFF.
The production integration must not reuse this registry as durable recovery.
