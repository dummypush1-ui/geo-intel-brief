# Geo Intel Brief

Geo Intel Brief brings together a public Geo news workspace, the Worldwide HSN
Code Finder and preserved BRICS/source tools. The app's existing layout and
runtime assets remain unchanged by repository cleanup.

**Live workspace:** https://geo-intel-brief.onrender.com/workspace

## Start here

Requirements: Node.js 22+.

```sh
npm install
npm run build       # rebuild the Finder web and offline outputs
npm run check       # build
npm start           # start the Node server
```

## Project map

See [the project map](docs/PROJECT_MAP.txt) for a short guide to the source
folders, build outputs and staged modules.

| Path | What it contains |
| --- | --- |
| `src/` | Finder source code, tariff/trade data and UI styling |
| `intelligence/geo/` | Geo news collection, processing and reports |
| `intelligence/brics/` | Preserved BRICS monitoring and report sources |
| `integration/` | Adapters, fixtures, feature preparation, reviews and evidence |
| `state/` | Stored data snapshots used by application code |
| `docs/archive/` | Exact historical README and embedded documentation archive |

## Feature status

The public workspace provides read-only news and trade context. When
`PUBLIC_NEWS_READ_ENABLED=true` and the required public disclosure, store
mapping and read-only credential checks pass, the full saved Geo collection is
searchable by default. Set `PUBLIC_NEWS_FULL_PAGES_ENABLED=false` to keep the
latest-100 sample view. Summary charts and CSV remain limited to the latest 100
articles. The Finder retains its offline search, detail, comparison, shortlist
and offline access. Optional Finder tools, maps, reports, code-news, accounts,
collectors, mail and AI paths remain guarded or default-off. Source presence
does not mean a feature is live or deployed.

Stored catalogue duties are reference data, not current official customs
rulings. External provider access, credentials, database configuration and
deployment behavior must be independently verified before enabling a guarded
feature.

## Verification

- **quality** — Finder build.
- **security** — Trivy, license checks and pip-audit.

See [GitHub Actions](https://github.com/dummypush1-ui/geo-intel-brief/actions)
for the latest results.

## Documentation archive

The complete previous README is preserved byte-for-byte in
[`docs/archive/original-readme.archive`](docs/archive/original-readme.archive).
Its 240 embedded historical Markdown sections remain accessible through
`scripts/doc_lookup.py`; former logical source paths and SHA-256 records are
preserved in the archive. The archive keeps historical
detail without turning the main project entry page into a 1 MB document.
