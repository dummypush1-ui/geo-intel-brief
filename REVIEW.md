# Current review boundary
Copyright (c) 2026 Push.

See [integration/FEATURE_STATUS.md](integration/FEATURE_STATUS.md) for current
works/blocked/missing/dropped scope. Earlier baseline-only status prose is
superseded, not a claim that every preserved feature now works in one app.

Original preservation: pinned source/config/template/script files in
preservation-manifest.json, namespace-only Python source changes and specific
classifier/dedupe/extraction hash checks. Original limitations remain visible.
Use current tests/test_preservation.py rather than obsolete baseline test counts.

Additive private routes now include Finder/news context, country signals,
weekly manual PDF, reference map and manual watched-country views. Preview
password access is optional single-worker configuration, not multi-user
accounts. All current readers/features retain explicit caps and supplied-data
limits. No live database/service/collector/mail/deploy proof follows.

Geo-only launcher is explicit default off. Its selected destination is
geo_intel/articles; no old BRICS newsbot/migration is needed in that composition.
Legacy isolated composition remains available, not silently replaced. Actual
mapping/credentials/source state and read factory must be reviewed at activation.

Before cutover: verify current service/config, exact storage identity/schema/
indexes and read authority, trusted proxy and host controls, worker/concurrency/
write deadlines, scheduler ownership and rollback. Separate explicit approvals
are required for live cutover, stopping old collectors, Render settings, mail,
live DB writes, polling and Telegram/WhatsApp delivery. Do not install a second
collector or run old setupTriggers. Destructive retention needs verified backup
policy and its own approval. No such effects were performed by this review.
