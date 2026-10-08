# Configuration guide

Copyright (c) 2026 Push. All rights reserved.

## How settings are loaded

The merged Flask entry points use a snapshot of the process environment. They do not automatically load a root `.env` file. Set values in the local process or the hosting service's environment. Never commit filled-in examples, MongoDB URIs, session keys, passwords or provider tokens.

`.env.example` is an inventory of historical/private settings, not a complete current public-mode recipe. Original Geo and BRICS configs call `load_dotenv`; that does not mean the merged Flask launcher does. Avoid loading legacy defaults into the merged app.

## Safe local deny mode

Set `PREVIEW_GEO_ONLY_ENABLED=true`, `PREVIEW_ACCESS_ENABLED=false`, `NEWS_READ_ENABLED=false`, `NEWS_EVENTS_READ_ENABLED=false` and `FINDER_NETWORK_PREVIEW_ENABLED=false`. Use `integration.private_router:app` and bind only to loopback. No credentials are needed. Workspace access is denied by design.

## Private password preview

Use `integration.private_router:app`. The Geo-only composition needs:

| Variable | Value or purpose |
|---|---|
| `PREVIEW_GEO_ONLY_ENABLED` | `true` |
| `PREVIEW_ACCESS_ENABLED` | `true` |
| `PREVIEW_ORIGIN` | Exact canonical HTTPS origin |
| `PREVIEW_PASSWORD_HASH` | Reviewed scrypt/PBKDF2 password hash, supplied securely |
| `PREVIEW_SESSION_KEY` | Random secret of at least 48 characters, supplied securely |
| `NEWS_READ_ENABLED` | Keep `false` for a no-database preview |
| `NEWS_EVENTS_READ_ENABLED` | Keep `false` unless separately reviewed |
| `FINDER_NETWORK_PREVIEW_ENABLED` | Keep `false` unless separately reviewed |
| `PREVIEW_TRUST_ONE_PROXY` | Default `false`; only enable after verifying the exact proxy topology |

Use one worker. This is a single-worker preview password gate, not durable multi-user account login. The private Geo reader additionally requires a separately verified mapping, actual read-only role, explicit URI and `NEWS_STORE_MAPPING_VERIFIED=true`.

## Public empty-sample mode

Use `public_preview106:app` only for an explicitly selected public preview. Required values:

```text
PREVIEW_PUBLIC_SAMPLE_ENABLED=true
PREVIEW_GEO_ONLY_ENABLED=true
PREVIEW_ACCESS_ENABLED=false
NEWS_READ_ENABLED=false
NEWS_EVENTS_READ_ENABLED=false
FINDER_NETWORK_PREVIEW_ENABLED=false
PREVIEW_ORIGIN=<exact canonical HTTPS origin>
```

No injected client is allowed. No stored news is read. Public passwords are not required in this mode; do not mistake public access for account authentication.

## Public stored-news mode

Use `public_live107:app`. All empty-sample settings above are still required, plus:

| Variable | Required value or purpose |
|---|---|
| `PUBLIC_NEWS_READ_ENABLED` | `true` |
| `NEWS_STORE_MAPPING_VERIFIED` | `true`, only after the exact mapping is checked |
| `PUBLIC_NEWS_DISCLOSURE_VERIFIED` | `true`, only after the displayed fields/audience are approved |
| `GEO_READONLY_CREDENTIAL_VERIFIED` | `true`, only after the actual Atlas role is checked |
| `GEO_DATABASE` | `geo_intel` |
| `GEO_ARTICLES_COLLECTION` | `articles` |
| `GEO_MONGODB_URI` | Dedicated read-only credential supplied securely |

Environment assertions are gates, not evidence that a credential is read-only or disclosure is authorized. Keep `NEWS_READ_ENABLED=false`: that private-mode flag is not the public reader switch.

The source's single-worker command is:

```bash
gunicorn public_live107:app --bind 0.0.0.0:$PORT \
  --workers 1 --threads 2 --timeout 30
```

This is a reference command, not an instruction to change a running service. See the [public reader notes](../integration/public_live107/README.md) for timeouts, cache, row limits and rollback. Actual hosting settings are not verified by this guide.

## Public response protections

`public_live107:app` installs E2 security headers by default. Once deployed, with no environment change, responses add X-Frame-Options, Permissions-Policy, Cross-Origin-Opener-Policy and X-Permitted-Cross-Domain-Policies. HTTPS responses (or a final `X-Forwarded-Proto` value of `https`) also add HSTS for 604800 seconds (7 days), without includeSubDomains or preload. Existing header values are not overwritten. `SECURITY_HEADERS_ENABLED=false` stops adding them, but cannot undo HSTS already cached by browsers.

E1 edge guard is different: it is off by default. `EDGE_GUARD_ENABLED=true` requires a separately confirmed Render single appended X-Forwarded-For hop. Its counters are per worker. Do not enable it from these documentation examples.

## Inactive operational settings

- `GEO_MONGODB_URI` and `BRICS_MONGODB_URI` isolate credentials for the retained projects. A shared legacy `MONGODB_URI` is not a safe merged default.
- `MERGED_MAIL_PATH=apps_script` and `MERGED_MAIL_ENABLED=false` describe the selected delivery direction. They do not mount the mail blueprint or create an Apps Script trigger. The bridge has its own `MAIL_V1_*` script properties; see [mail mount design](../feature_mail_mount/DESIGN.md).
- Finder provider pools, `AISSTREAM_KEY`, `APP_SECRET`, updater GitHub tokens and Comtrade keys belong to separate preserved services. Their presence does not enable them in public Flask.
- Legacy `ENABLE_*` settings can activate sends, scraping or cleanup in the original engines. Leave them off in development and do not launch those engines casually.
- Optional `trafilatura`/`gnews` dependencies are outside the reviewed 25-package closure. Installing the original Geo requirements adds these packages even when feature flags are off.

Do not enable collection, mail, provider calls, account persistence or cleanup as part of README/folder cleanup. Each needs its own reviewed integration and cutover.
