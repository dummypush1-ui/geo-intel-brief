# Public empty-sample preview106

Explicit opt-in public preview. No stored news, passwords, provider keys, notes,
DB connection, collector, mail, write routes, PDF generation or live network
Finder. Default false delegates unchanged private launcher, preserving rollback.
Public true requires Geo-only true, access false, article/events reads false and
Finder network false. Injected clients rejected before construction. Canonical
HTTPS origin required; unexpected host rejected. Fixed empty reader is public
sample scope, not news DB. GET/HEAD exact allowlist; other methods denied. Health
retains existing public staging status. Root redirects to workspace. Public label
in HTML; no-store/noindex/CSP remain. Original Finder shell with saved keys is
not exposed: iframe is sanitized self-contained offline snapshot (no localStorage,
fetch or SW registration). Live video/channel controls and heavier weekly/BRICS
links removed from public home. No old source or historical audit bytes changed.

User-operated Render settings, only after reviewed save:
Start Command:
gunicorn public_preview106:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 30

PREVIEW_PUBLIC_SAMPLE_ENABLED=true
PREVIEW_GEO_ONLY_ENABLED=true
PREVIEW_ACCESS_ENABLED=false
NEWS_READ_ENABLED=false
NEWS_EVENTS_READ_ENABLED=false
FINDER_NETWORK_PREVIEW_ENABLED=false
PREVIEW_TRUST_ONE_PROXY=false
PREVIEW_ORIGIN=https://geo-intel-brief.onrender.com
PYTHON_VERSION=3.10.12

Password hash/session key ignored in public mode; can remain for rollback, never
shared in chat or repository. Secret URI not used. Do not turn live reads on in
public mode. Rollback: PREVIEW_PUBLIC_SAMPLE_ENABLED=false and original private
settings/access credentials, or restore prior private_router start command.
Public output uses empty sample/unavailable panels honestly, not fake live rows.

Executed8 public-mode focused tests PASS, including private rollback. Full1166
configured tests PASS, existing1expected limiter failure/1optional pikepdf skip.
Local390/1280browser screenshots visually inspected: readable, no overflow,
clear empty-sample labels, zero pageerrors/external requests, offlineFinder works.
Local HTTPS authority rewrite used ONLY in browser harness, never production.
Render proxy behavior requires live200 verification after user switches entrypoint.
