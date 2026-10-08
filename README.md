# Geo Intel Brief

Copyright (c) 2026 Push. All rights reserved.

Geo Intel Brief brings geopolitical news, trade-code lookup and BRICS source features into one codebase. The Flask workspace connects stored news with country views, story groups, trade context, exports and report tools. The original Finder, Geo and BRICS code remains in the repository.

**The merge is in progress.** A public read-only news preview is implemented, but collectors, mail, account login and the full Finder provider connection are not mounted into that public launcher. Prepared code and passing local tests do not mean a feature is live.

## Start here

- [Architecture and code map](docs/ARCHITECTURE.md)
- [Configuration guide](docs/CONFIGURATION.md)
- [Sanctions operator policy](updater_runtime/SANCTIONS-POLICY.md) - manual reviewedHashes, no approval endpoint
- [GST grounding](updater_runtime/GST-GROUNDING.md) - operator_reviewed required
- [Monitor health](updater_runtime/MONITOR-HEALTH.md) - pending_issues and uncertain outcomes
- [Folder cleanup proposal](docs/FOLDER-PLAN.md) - a plan, not a file move
- [Feature history and limits](integration/FEATURE_STATUS.md) - historical checkpoints; check the newer module-specific notes too
- [Security notes](SECURITY.md)
- [License](LICENSE)

## Entry points

| Entry point | Purpose | Important limit |
|---|---|---|
| `integration.private_router:app` | Deny-by-default private preview | Default settings do not grant workspace access or enable reads. Password preview is not account login. |
| `public_preview106:app` | Explicit public empty-sample preview | No stored-news client. All public-mode gates must match. |
| `public_live107:app` | Explicit public Geo stored-news preview | Read-only `geo_intel/articles`, latest up to 100 documents, bounded cache and public field filtering. Requires separately verified disclosure and database role. |
| `server.js` | Preserved Finder updater service | Starts a refresh timer. **Not** the merged web app. |
| `proxy.js` | Preserved Finder AI/AIS proxy | Separate provider/network service, not mounted by the public Flask launcher. |
| `intelligence/geo/`, `intelligence/brics/` | Preserved original engines | Can connect, schedule, send or clean up. Do not launch them as a shortcut to starting the merge. |

There is no single "enable everything" switch. Do not use `npm start` for the Flask workspace: it starts the updater.

## Run a safe local check

Use Python 3.10 or a separately reviewed compatible version. Node 22 or newer is needed for the Finder's Node tests and built-in WebSocket support. Run from the repository root.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-staging.txt
```

`requirements-staging.txt` installs the basic Flask/Mongo preview dependencies. It is not the full offline test closure, a hash-locked installation or proof of the deployed environment. Package installation accesses the configured package index. This path pins Gunicorn 22.0.0, as do the frozen locks. The security candidate lock pins Gunicorn 23.0.0 for the reviewed CVE fixes. A deployment should use that candidate only after its install is verified in the intended environment; do not infer deployment safety from this basic preview install.

With a clean local environment, start the no-read, deny-by-default launcher:

```bash
PREVIEW_GEO_ONLY_ENABLED=true \
PREVIEW_ACCESS_ENABLED=false \
NEWS_READ_ENABLED=false \
NEWS_EVENTS_READ_ENABLED=false \
FINDER_NETWORK_PREVIEW_ENABLED=false \
gunicorn integration.private_router:app \
  --bind 127.0.0.1:8000 --workers 1 --threads 2 --timeout 30
```

This is a startup check, not an unlocked demo. `/workspace` returning 403 is expected. Keep database URIs and provider keys out of this local check. Unset inherited operational variables before using a development shell.

For an empty public preview or private password preview, use the exact mode-specific settings in [Configuration](docs/CONFIGURATION.md). Public modes require a canonical HTTPS origin; changing the origin check to make HTTP work would weaken the boundary.

## Tests

A small offline integrity check uses only the standard library:

```bash
PYTHONPATH=tests python3 -m unittest \
  test_preservation test_package_manifest test_collector122_inventory
```

The full configured suite uses additional dependencies, verified parser artifacts and Node:

```bash
PYTHONPATH=.:collector108_prep python -m unittest discover -s tests
```

See [the dependency build notes](integration/dependency_build/README.md), [the current PDF profile](integration/pypdf_remediation105/README.md) and [the future deployment contract](integration/security_maintenance94/DEPLOY-CONTRACT.md). Some historical checks need their recorded artifact cache. Missing artifacts are unverified, not passed. Do not treat old test counts in documents as a current full-suite result.

The historical offline candidate lock still records its missing wheel/hash. The newer `integration/security_candidate/requirements-security-candidate.txt` has verified package hashes and a hashed `sgmllib3k` source archive; its install and `pip check` were tested separately. Its legacy source-build bootstrap is not a fully hash-locked build chain. The frozen future-deploy lock remains separate and requires verified wheel artifacts, including a locally built `sgmllib3k` wheel. Neither source tests nor a candidate install prove the deployed environment.

The current source gate is 1469 root cases plus 285 collector cases, 10 checks cases and 26 world cases outside root discovery. The staging manifest `tests` field records only 1469. See [exact gate commands](docs/TEST-GATES.md).

## Configuration and safety

Use environment variables, not committed credentials. `.env.example` lists the historical and private settings; the configuration guide also explains newer public-mode gates absent from that example. The Flask launchers read the process environment directly; copying `.env.example` to `.env` does not load it automatically.

- A read facade does not make a privileged MongoDB credential read-only. Verify the actual Atlas role.
- Public news is a bounded stored-news view, not full-database search, whole-history totals or source fact-checking.
- Apps Script is the selected merged mail path. SMTP remains preserved legacy code, not an automatic fallback.
- Collector preparation packages and mail/account/provider fixtures need separate mounting, source review and activation.
- Keep source-policy restrictions, credential rotation and cutover decisions separate from code cleanup.
- Stop old collectors only after a reviewed migration and explicit cutover decision. Two writers can create duplicates.

This README describes source behavior, not the current Render settings, database state or provider-account permissions. No production changes are needed for this documentation cleanup.
