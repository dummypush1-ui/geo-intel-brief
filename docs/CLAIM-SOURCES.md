# Documentation claim checks

Inspected source base: 20649f625838f74a429b61702c9d9a8e2fdaca84. These are source contracts, not deployed-state checks.

| Documentation claim | Source evidence |
|---|---|
| Process environment snapshot, no automatic root dotenv | `integration/private_router.py:2-10`; `integration/public_live_builder.py:143` and `integration/public_preview_builder.py:73` (final `app=build_...(dict(os.environ))` statements; use symbol search if line numbers shift) |
| `PREVIEW_GEO_ONLY_ENABLED=true` selects Geo-only; default false | `integration/preview_launcher.py:13-25` |
| Private `PREVIEW_ACCESS_ENABLED`, `PREVIEW_ORIGIN`, `PREVIEW_PASSWORD_HASH`, `PREVIEW_SESSION_KEY` | `integration/preview_access.py:92-96` |
| HTTPS canonical origin | `integration/preview_access.py:18-22`; `integration/public_preview_builder.py:34-38`; `integration/public_live_builder.py:70-74` |
| scrypt/PBKDF2 password hash accepted | `integration/preview_access.py:23-24` validation; `:12` imports `check_password_hash` |
| Session secret at least 48 characters | `integration/preview_access.py:85-86` |
| `PREVIEW_TRUST_ONE_PROXY=false` default, optional explicit true | `integration/preview_access.py:97-100`; `.env.example:147` (locate variable if lines change) |
| Empty public mode exact flags: `PREVIEW_PUBLIC_SAMPLE_ENABLED=true`, `PREVIEW_GEO_ONLY_ENABLED=true`, `PREVIEW_ACCESS_ENABLED=false`, `NEWS_READ_ENABLED=false`, `NEWS_EVENTS_READ_ENABLED=false`, `FINDER_NETWORK_PREVIEW_ENABLED=false` | `integration/public_preview_builder.py:26-33` |
| No injected client in public sample | `integration/public_preview_builder.py:29,46` |
| `PUBLIC_NEWS_READ_ENABLED` false fallback / exact true enable | `integration/public_live_builder.py:58-60` |
| Public live mode requires all public sample flags plus `NEWS_STORE_MAPPING_VERIFIED=true`, `PUBLIC_NEWS_DISCLOSURE_VERIFIED=true`, `GEO_READONLY_CREDENTIAL_VERIFIED=true` | `integration/public_live_builder.py:61-66` |
| Exact `GEO_DATABASE=geo_intel`, `GEO_ARTICLES_COLLECTION=articles`; `GEO_MONGODB_URI` required | `integration/public_live_builder.py:67-69,87`; credential role is operator assertion, not introspected |
| Private article reads require access, mapping review, URI; events separately gated | `integration/geo_only_runtime.py:23-46` |
| `GEO_MONGODB_DB_NAME` versus `GEO_DATABASE` conflict refused | `integration/preview_launcher.py:18-20` |
| Separate Geo/BRICS URI names and legacy fallback | `integration/storage_settings.py:20-30` |
| Public latest up to 100 rows; malformed rows may reduce count | `integration/public_live_builder.py:18,26-27,87,101`; `integration/storage_reader.py:23` sorts by `created_at` |
| Per-process successful read cache 60 seconds | `integration/public_live_builder.py:92-103` |
| Database read failure clears cache, closes client and latches until restart after repair | `integration/public_live_builder.py:96,104-108`; no reset branch exists in the closure |
| Public protected route authorization is GET/HEAD-only allowlist | `integration/public_live_builder.py:76-81`; `integration/public_preview_builder.py:40-45`; public framework health/error/automatic OPTIONS responses are not a write capability |
| Single-worker run guidance | `integration/public_live107/README.md:45-46`; `integration/public_preview106/README.md:16-18`; private limiter/session state in `integration/preview_access.py:26-35`. The code does not enforce Gunicorn worker count. |
| `MERGED_MAIL_PATH=apps_script`, `MERGED_MAIL_ENABLED=false` default, no SMTP fallback | `integration/mail_bridge.py:10-17`; `.env.example:127-131` |
| Mail mount not imported by existing launchers | `feature_mail_mount/DESIGN.md:5-9`; no `feature_mail_mount` imports in `public_live107.py`, `public_preview106.py`, `integration/private_router.py`, `integration/preview_launcher.py` or `integration/news_api.py` |

## Audit hash scope

`integration/dependency_audit/audit.json:583` contains `source_manifest_sha256`. It hashes the canonical JSON list in `integration/dependency_audit/import-inventory.json` -> `source_baseline.files`, not the root `staging-manifest.json`.

The test `Tests.test_source_manifest_and_ast_inventory_consistency` in `tests/test_dependency_audit.py` recomputes the list hash, checks source bytes/AST and compares the scoped inventory. The current source hash is `722b33caa7625c6fa23e9c536f69765d1f84e1d5fcb518227cf88a904da6669e`, recomputed from the inspected base. Older dependency receipts remain historical records, not current install evidence.

## Current additions

- `public_live107.guarded_public_app` installs E2 security headers by default, before optional E1. `integration/security_headers.py` defines HSTS 604800 on secure requests or a final HTTPS forwarded-proto value, plus XFO, Permissions-Policy, COOP and XPCDP. Existing response header values are preserved.
- `integration/edge_guard.py` is off unless `EDGE_GUARD_ENABLED=true`. Enabling requires a separate Render single appended XFF-hop topology check. This document does not confirm that topology.
- Root discovery includes 25 E1/E2 tests. Collector 285, checks 10 and world 26 are separately discovered. Commands and expected counts are in `TEST-GATES.md`; source tests are not deployment approval.

Factory176source correction: public_live107/public_preview106 are thin compatibility WSGI entries. Shared public_live_builder/public_preview_builder/news_api create no app/client at import. news_api:app is lazy on WSGI access, preserving factory module patch targets. production_entry uses guarded_public_app (one security headers hook, optional edge stays defaultOFF). Runtime read failure latch/restart contract unchanged.
