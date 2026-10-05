# Private Geo + trade Finder merge
Copyright (c) 2026 Push.

Current local feature status: [integration/FEATURE_STATUS.md](integration/FEATURE_STATUS.md).
This is a tested private staging tree, not a deployed or fully complete merged
app. Existing source is preserved; additive routes use private access and
supplied/explicitly gated readers. No live cutover is certified here.

The default-off PREVIEW_GEO_ONLY_ENABLED launcher switch selects the reviewed
Geo-only branch only when explicitly true. Reads remain separately off/gated.
That branch has no default database client factory, so read-on through the
current private entrypoint fails closed pending reviewed live composition.
The legacy isolated branch is retained for rollback; missing BRICS settings do
not silently select Geo-only. Use neither branch as permission for live reads.

Country signals, weekly manual PDF, reference map, Finder/news context and
manual country watches have local routes/UI. They are bounded supplied-data
features, not full-history coverage, live status or delivery. Accounts and
original-export HTTP are separate dev fixtures, not merged production routes.

Original Geo/BRICS collector/report/config source remains hash-pinned in
preservation-manifest.json. Processing parity checks are narrower than complete
runtime parity. Geo web import-time connections and old sends/cleanup/timers
must not be imported or activated casually. SMTP is preserved legacy only;
selected merged delivery path is Apps Script, still not active.

Selected stored-news destination is geo_intel/articles, subject to current
source/credential/schema review. Geo-only excludes old BRICS newsbot access;
no migration, rename/drop or cleanup was performed. Configure URI only through
operator secret environment, never source/browser. This document does not
assert any current external service or database state.

Local check in the configured Python environment:
PYTHONPATH=tests python -m unittest discover
Dependencies and per-feature caveats are in integration/*LIMITS.md and package
README files. Last full author suite: 830 tests at save 60, with 1 skip and 1 expected failure.
After a workspace reset, the local tree is partial; that full suite has not been
rerun. Saves 61-65 have focused evidence in their LIMITS files, not a new full
suite count. Save 65 has 22 native-PyMongo fake-driver tests passing. Unsupported
multiple account limiter instances remain explicitly pinned.
