# Folder arrangement proposal

Copyright (c) 2026 Push. All rights reserved.

This is a proposal only. No source, feature, asset, evidence, configuration or workflow file is moved or deleted by the documentation patch.

## First: make the existing tree understandable

1. Keep runtime and original-code paths unchanged.
2. Add the root README and `docs/` navigation guides.
3. Link each preparation package's design note from an inventory rather than renaming packages during active development.
4. Label historical dependency receipts and current installation profiles clearly. Do not erase evidence to reduce alert counts.

This gives a clearer repository without breaking imports, relative file reads, public asset allowlists, generated Finder output or preservation hashes.

## Later: proposed target layout

```text
apps/
  workspace/          # selected Flask entry points
  finder/             # Finder static input/output and separate Node services
engines/
  geo/                # original Geo engine
  brics/              # original BRICS engine
integration/          # shared adapters, readers and contracts
preparation/
  collectors/         # collector stage packages, preserved by identity
  mail/
  finder/
  related/
docs/
  architecture/
  configuration/
  evidence/           # dated, immutable receipts with source-path mappings
tests/
scripts/
```

The target layout is not ready to apply wholesale. `integration/` contains both serving modules and evidence; separating them needs an explicit import/data-path map. Root Finder filenames are loaded by builds and readers, and `intelligence/*` files are hash-pinned.

## Migration gates, one slice at a time

- Inventory every Python import, dynamic import, Node path, HTML asset reference, source-file read, manifest path and test fixture before moving a slice.
- Preserve feature behavior and add temporary compatibility entry points only where reviewed.
- Record old-to-new paths and update preservation/integrity metadata without rewriting historical evidence.
- Verify generated Finder branding/data, private/public route allowlists and forbidden-path tests.
- Run targeted tests and the configured full suite; inspect the served UI and PDFs for visual regressions.
- Have the runtime owner review build/start paths and rollback separately. Do not change hosting or trigger a deployment merely to tidy folders.
- Leave `.github/workflows/` untouched in this work. Any eventual workflow path migration is an owner-managed follow-up.

## Do not consolidate collector stages blindly

The numbered collector packages hold different parser, fetch, selection, receipt and composition contracts. A later stage imports earlier reviewed stages; the folders are not proven redundant copies. Before choosing a single production collector, document the dependency graph, preserve its audit history and prove behavioral parity. Retain every working feature and fail-closed limit.

The immediate recommendation is documentation-only navigation. Defer physical rearrangement until the active merge and runtime mounting have a stable, reviewed boundary.
