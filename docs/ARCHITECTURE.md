# Architecture and code map

Copyright (c) 2026 Push. All rights reserved.

## Request flow

```text
Flask entry point
  public_live107 / public_preview106 / integration.private_router
    -> explicit mode and access gates
    -> integration.news_api.create_app
       -> bounded reader and public field normalization
       -> news, country, story, map, export and report adapters
       -> integration/ui and approved Finder/branding assets
```

The public live entry point injects a find-only reader for `geo_intel/articles`. It selects up to 100 documents by `created_at`, normalizes the approved public fields and caches successful reads for 60 seconds per process. Malformed rows can reduce the displayed count. A database failure latches the reader unavailable until process restart after repair; it is not shown as a successful empty collection.

The public entry point allows a narrower GET/HEAD route set than the private app. It serves a self-contained offline Finder snapshot, not the original provider-connected shell. Weekly PDF, private POST actions, event reads and account/mail operations are outside that public route set.

`integration.preview_launcher` selects the explicit Geo-only branch or the retained isolated legacy branch. `integration.geo_only_runtime` composes private access with optional reviewed article/event reads. These launchers do not import the original collector applications as a complete live merge.

The public live wrapper adds default-on E2 response headers and an optional, default-off E1 edge guard. See [Configuration](CONFIGURATION.md).

## Existing folders

| Location | Responsibility | State |
|---|---|---|
| `integration/` | Shared Flask API, adapters, access gates, readers, cross-project models and review records | Mixed runtime, test support and historical evidence; read each feature's limits |
| `integration/ui/` | Workspace, country, map, report and Finder offline UI | Assets served through explicit allowlists |
| `integration/branding/` | Workspace logos, icons and metadata | Served branding |
| `src/`, root HTML/JS/CSS assets, `vendor/` | Original Finder data, build input and static output | Retained; paths are referenced by builds, readers and tests |
| `proxy_runtime/`, `updater_runtime/` | Finder proxy safety and refresh/update helpers | Separate from public Flask mounting |
| `intelligence/geo/` | Original Geo collectors, processing, storage, reports and web app | Retained engine; importing operational modules can have effects |
| `intelligence/brics/` | Original BRICS engine, source config, reports and web app | Retained engine, not public Geo stored-news source |
| `collector108_prep/` through `collector130_prep/` | Successive collector preparation stages, receipts, parsers and bounded composition | Preparations, not automatically active collectors |
| `feature_mail_prep/`, `feature_mail_mount/` | Mail contracts, Mongo receipt/control store, blueprint and Apps Script bridge | Mount implementation exists; existing public/private launchers do not import it |
| `feature_finder_prep/` | Provider mount policy and served-copy preparation | Not a live authenticated provider connector |
| `feature_world_views/` | Supplied world detail/filter/export views | Source module and fixtures, not live world retrieval or automatic mounting |
| `checks/` | Collector facade, production wrapper and source drift checks | Ten separate cases outside root discovery |
| `feature_related_prep/` | Related-news preparation | Separate from automatic production activation |
| `tests/` | Python and Node-related regression contracts | Includes historical artifact and fixture checks |
| `scripts/` | Integrity metadata, connection audit and provenance helpers | Maintenance tools, not a deploy command |
| `state/`, `legacy-config/` | Finder updater state and retained workflow/config sources | Keep out of new deployment assumptions |

## Cross-project connections

The integration layer contains news-to-Finder context, country signals/pages, related-story groups, stored-news exports, original report adapters, source/tariff evidence and map data. `integration/cross-connections.json` records the earlier connection design. These connections are bounded by the selected launcher and reader; source retention alone does not expose every original feature.

## Boundaries to preserve

- Keep the original source and evidence intact while improving navigation.
- Do not move hash-pinned files without a reviewed manifest migration.
- Preserve the public field allowlist and private route/access separation.
- Do not reuse the public read-only client for mail acknowledgements or collection writes.
- Mount collectors, durable account login, provider calls and mail separately with reviewed credentials, limits and permissions.
- Node updater/proxy services and legacy Geo/BRICS launchers are distinct operational processes, not alternative ways to run the same app.

For proposed folder changes, see [FOLDER-PLAN.md](FOLDER-PLAN.md). No files have been moved by this documentation patch.
