# Geo Intel Brief — project map

This guide is the quick route into the repository. It does not replace the
preserved source notes or claim that every prepared feature is live.

## Quick commands

Requires Node.js 22 or newer.

```sh
npm install
npm run build       # rebuild the Finder hosted shell and offline file
npm run check        # build
npm start            # start the Node server
```

The canonical end-to-end check is the GitHub Actions **quality** workflow (build).

## Where the real app lives

| Area | Purpose | Safe editing rule |
| --- | --- | --- |
| `src/` | Finder UI, styles, tariff/trade datasets and app source | Edit source here, then run `npm run build`; do not hand-edit generated bundles |
| `build.mjs` | Builds the hosted Finder, offline single-file version, service worker and versioned data | Treat it as the output generator |
| `index.html`, `offline.html`, `sw.js`, `data.*.js` | Generated/packaged Finder output | Regenerate from source instead of manually changing |
| `server.js`, `proxy.js`, `production_entry.py` | Server/proxy and guarded Python application entry points | Check related tests and configuration before changing |
| `intelligence/geo/` | Geo-news collection, processing, reports and dashboard code | Keep its source-preservation checks green |
| `intelligence/brics/` | BRICS monitoring and report sources | Prepared/preserved code is not proof that a service is deployed |
| `state/` | Stored trade/data snapshots used by the application | Check data consumers and data provenance before replacing files |
| `assets/`, `vendor/` | UI assets and vendored browser/runtime dependencies | Preserve licensing and dependency provenance |

## Why there are many files

The repository brings multiple source projects together. Not every path is a
production module:

- `tests/` and `checks/` protect UI/build behavior, application contracts,
  safety gates and source-preservation expectations.
- `integration/` contains adapters, review candidates, fixtures, manifests,
  evidence and feature work at different readiness levels. A file existing
  here does not mean the feature is enabled or deployed.
- `collector*_prep/` contains versioned collector/parser preparation, tests,
  pins and compatibility records. Some paths are imported by later stages;
  similarly named modules are not automatically duplicates.
- `runtime_build/`, `runtime_executor27c/`, `workflow_executor29b/`,
  `workflow_package29/` and `portable_validation28*/` retain staged build,
  packaging and review evidence.
- `README.md` is the short project entry page. The complete former README and
  its 240 byte-checked historical Markdown sections are preserved in
  `docs/archive/original-readme.archive`. `scripts/doc_lookup.py` reads
  that archive while keeping the previous virtual document paths compatible.
- `preservation-manifest.json` and `staging-manifest.json` record hashes and
  sizes. Changes to covered source files must update the relevant manifest.

## Keep every feature and layout while simplifying

1. Change one logical module at a time; keep the current UI and public paths.
2. Do not delete or merge files based on matching hashes alone. Check imports,
   data consumers, tests, generated-artifact inputs and manifest references.
3. Keep guarded/default-off features guarded unless separately reviewed.
4. Run `npm run check` after Finder changes and the full quality/security
   workflows before accepting a refactor.
5. Record the result of each phase so a failed change can be isolated or
   reverted without losing unrelated features.

The public workspace is linked from the root README. Feature readiness and
limits in that file take precedence over a directory name or the presence of
source code.
