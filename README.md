# Geo Intel Brief

Geo Intel Brief brings together a public Geo news workspace, the Worldwide HSN
Code Finder and preserved BRICS/source tools.

**Live workspace:** https://geo-intel-brief.onrender.com/workspace

## Start here

Requirements: Node.js 22+.

```sh
npm install
npm run build       # rebuild the Finder web and offline outputs
npm run check       # build outputs
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

The public workspace provides read-only news and trade context. The Finder
retains its search, detail, comparison, shortlist and offline capabilities.
Some maps, reports, code-news, accounts, collectors, mail and AI-related paths
are guarded or default-off. Source presence does not mean a feature is live,
approved or deployed; the archived records preserve the evidence and limits.

Stored catalogue duties are reference data, not current official customs
rulings. External provider access, credentials, database configuration and
deployment behavior must be independently verified before enabling a guarded
feature.

## Verification

- **quality** — Finder build.
- **security** — Trivy, license checks and pip-audit.

The repository does not include automated regression test suites. See
[GitHub Actions](https://github.com/dummypush1-ui/geo-intel-brief/actions)
for the latest build and security results.

## Documentation archive

The complete previous README is preserved byte-for-byte in
[`docs/archive/original-readme.archive`](docs/archive/original-readme.archive).
Its 240 embedded historical Markdown sections remain accessible through
`scripts/doc_lookup.py`; former logical source paths and SHA-256 records are
preserved in the archive. The archive keeps historical detail without turning
the main project entry page into a 1 MB document.
