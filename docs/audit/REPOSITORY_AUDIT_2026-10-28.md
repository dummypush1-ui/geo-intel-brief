# Repository audit baseline

- Audited branch: `main`
- Commit: `96a5c95fb523058429dd1791a9111dfc66a6429a`
- Date: 2026-10-28
- Tree complete: `true`
- Files (Git blobs): **1165**
- Directories (Git trees): **161**
- Total tree entries: **1326**
- Exact-content duplicate groups (same Git blob SHA): **56**
- Paths participating in those groups: **125**

## Findings

1. `integration/` contains **569** files and is the largest top-level area. It includes feature candidates, adapters, fixtures, review records, manifests and evidence; source presence alone does not mean production activation.
2. `src/` contains **98** files and is the primary Finder source area. Generated root outputs must be rebuilt from source, not hand-edited.
3. `intelligence/` contains **60** files for Geo and BRICS source modules.
4. Several versioned `collector*_prep/`, `runtime_*`, `workflow_*` and `portable_validation*` folders hold preparation or validation material. Similar names or matching bytes do not prove a path is unused.
5. Duplicate blob hashes prove byte-for-byte equality only. They do **not** prove that paths can safely be deleted or merged: imports, deployment manifests, preservation hashes, build inputs and historical evidence must be checked first.
6. The root includes very large generated outputs (including `index.html`, `offline.html`, and versioned `data.*.js`). Preserve generated output behavior and regenerate through the existing build pipeline.
7. Guarded/default-off features should remain guarded unless independently reviewed. Secrets and environment values must not be copied into audit output.

## Top-level file counts

| Area | Files |
|---|---:|
| `integration` | 569 |
| `src` | 98 |
| `intelligence` | 60 |
| `runtime_build` | 51 |
| `(root)` | 44 |
| `collector112_prep` | 39 |
| `workflow_executor29b` | 38 |
| `collector128_prep` | 37 |
| `collector108_prep` | 21 |
| `updater_runtime` | 14 |
| `feature_carrier_prep` | 13 |
| `feature_world_views` | 11 |
| `collector109_prep` | 10 |
| `runtime_executor27c` | 10 |
| `state` | 10 |
| `portable_validation28b` | 9 |
| `feature_mail_mount` | 8 |
| `.github` | 7 |
| `workflow_package29` | 7 |
| `collector113_prep` | 6 |
| `collector114_prep` | 6 |
| `collector117_prep` | 6 |
| `portable_validation28` | 6 |
| `proxy_runtime` | 6 |
| `scripts` | 6 |
| `collector110_prep` | 5 |
| `collector115_prep` | 5 |
| `collector130_prep` | 5 |
| `collector111_prep` | 4 |
| `collector116_prep` | 4 |
| `collector118_prep` | 4 |
| `collector119_prep` | 4 |
| `collector120_prep` | 4 |
| `collector121_prep` | 4 |
| `collector124_prep` | 4 |
| `collector122_prep` | 3 |
| `collector123_prep` | 3 |
| `collector129_prep` | 3 |
| `feature_finder_prep` | 3 |
| `feature_mail_prep` | 3 |
| `feature_related_prep` | 3 |
| `collector125_prep` | 2 |
| `collector126_prep` | 2 |
| `collector127_prep` | 2 |
| `docs` | 2 |
| `legacy-config` | 2 |
| `assets` | 1 |
| `vendor` | 1 |

## File extension counts

| Extension | Files |
|---|---:|
| `.py` | 529 |
| `.json` | 206 |
| `.txt` | 107 |
| `.ts` | 96 |
| `.js` | 59 |
| `.mjs` | 29 |
| `.css` | 26 |
| `.html` | 24 |
| `.yml` | 10 |
| `.log` | 9 |
| `.gs` | 7 |
| `.png` | 7 |
| `.cjs` | 7 |
| `.lock` | 7 |
| `.yaml` | 6 |
| `[no extension]` | 6 |
| `.sh` | 5 |
| `.svg` | 2 |
| `.webmanifest` | 2 |
| `.tsv` | 2 |
| `.example` | 1 |
| `.gitignore` | 1 |
| `.md` | 1 |
| `.gif` | 1 |
| `.archive` | 1 |
| `.ico` | 1 |
| `.idx` | 1 |
| `.jsonl` | 1 |
| `.csv` | 1 |
| `.bin` | 1 |

## Exact-content duplicate groups

1. SHA `5ebc522b395b42886d56e74abdfb4fe296931c32` (2 paths):
   - `collector108_prep/collection_only.gs`
   - `collector109_prep/wiring/collection_only.gs`

2. SHA `5dca2aa0a43290de94cb1fa7b739f1f92aefef6b` (3 paths):
   - `collector112_prep/sdk-pins.json`
   - `collector128_prep/sdk-pins.json`
   - `integration/feedparser_audit/sdk-pins.json`

3. SHA `a9607801c13a70740ed8b19e62475b1d2d89dd64` (2 paths):
   - `collector112_prep/vendor/feedparser/__init__.py`
   - `collector128_prep/vendor/feedparser/__init__.py`

4. SHA `1fe40979cfe056117485665513fd8e2392603aca` (2 paths):
   - `collector112_prep/vendor/feedparser/api.py`
   - `collector128_prep/vendor/feedparser/api.py`

5. SHA `2837838ba6afe7e823caf6bc6a1b9ece4020b66f` (2 paths):
   - `collector112_prep/vendor/feedparser/datetimes/__init__.py`
   - `collector128_prep/vendor/feedparser/datetimes/__init__.py`

6. SHA `99416f664aa6512775b58979bbf3ed4cd20b2a7d` (2 paths):
   - `collector112_prep/vendor/feedparser/datetimes/asctime.py`
   - `collector128_prep/vendor/feedparser/datetimes/asctime.py`

7. SHA `3a4db71485bd9d974eb8cb35d91af8b85ca97324` (2 paths):
   - `collector112_prep/vendor/feedparser/datetimes/greek.py`
   - `collector128_prep/vendor/feedparser/datetimes/greek.py`

8. SHA `63fa9afd1b67b0f1448afc6bccd86d828d972edb` (2 paths):
   - `collector112_prep/vendor/feedparser/datetimes/hungarian.py`
   - `collector128_prep/vendor/feedparser/datetimes/hungarian.py`

9. SHA `e78764592f746dfb7c8ffc82fea7fc5bae6fa6e8` (2 paths):
   - `collector112_prep/vendor/feedparser/datetimes/iso8601.py`
   - `collector128_prep/vendor/feedparser/datetimes/iso8601.py`

10. SHA `5fe4eb6f9d240a5c6551fb8a85e49e9539217bba` (2 paths):
   - `collector112_prep/vendor/feedparser/datetimes/korean.py`
   - `collector128_prep/vendor/feedparser/datetimes/korean.py`

11. SHA `e53e5ff67b607923e3d07390348e78213d9037d6` (2 paths):
   - `collector112_prep/vendor/feedparser/datetimes/perforce.py`
   - `collector128_prep/vendor/feedparser/datetimes/perforce.py`

12. SHA `12e699c84f9abc3cffb33966e8fc3d037f886a0f` (2 paths):
   - `collector112_prep/vendor/feedparser/datetimes/rfc822.py`
   - `collector128_prep/vendor/feedparser/datetimes/rfc822.py`

13. SHA `9b71af1fa35b8803bd33bdd1b05449ec75d25598` (2 paths):
   - `collector112_prep/vendor/feedparser/datetimes/w3dtf.py`
   - `collector128_prep/vendor/feedparser/datetimes/w3dtf.py`

14. SHA `5ae74af68948d203cb9f0be22a1d56a267c508c6` (2 paths):
   - `collector112_prep/vendor/feedparser/encodings.py`
   - `collector128_prep/vendor/feedparser/encodings.py`

15. SHA `0da8152ff3510100189125c04add7db2c448e14e` (2 paths):
   - `collector112_prep/vendor/feedparser/exceptions.py`
   - `collector128_prep/vendor/feedparser/exceptions.py`

16. SHA `0aae18f6a80d12f03a480d7c23756a4f0697e4aa` (2 paths):
   - `collector112_prep/vendor/feedparser/html.py`
   - `collector128_prep/vendor/feedparser/html.py`

17. SHA `1516eabfde971376a622d1eeb9ea6563a6178eb2` (2 paths):
   - `collector112_prep/vendor/feedparser/http.py`
   - `collector128_prep/vendor/feedparser/http.py`

18. SHA `c4265e750f42bc5bc691d585729e6b105ef92faa` (2 paths):
   - `collector112_prep/vendor/feedparser/mixin.py`
   - `collector128_prep/vendor/feedparser/mixin.py`

19. SHA `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` (12 paths):
   - `collector112_prep/vendor/feedparser/namespaces/__init__.py`
   - `collector112_prep/vendor/feedparser/parsers/__init__.py`
   - `collector128_prep/vendor/feedparser/namespaces/__init__.py`
   - `collector128_prep/vendor/feedparser/parsers/__init__.py`
   - `intelligence/brics/__init__.py`
   - `intelligence/brics/collectors/__init__.py`
   - `intelligence/brics/processing/__init__.py`
   - `intelligence/brics/reports/__init__.py`
   - `intelligence/geo/__init__.py`
   - `intelligence/geo/collectors/__init__.py`
   - `intelligence/geo/processing/__init__.py`
   - `intelligence/geo/reports/__init__.py`

20. SHA `cb2b2a98ca246e6ad8e621a690166788c9475f7c` (2 paths):
   - `collector112_prep/vendor/feedparser/namespaces/_base.py`
   - `collector128_prep/vendor/feedparser/namespaces/_base.py`

21. SHA `88b70013d3f6cb662df2e99908706310cf9bef2c` (2 paths):
   - `collector112_prep/vendor/feedparser/namespaces/admin.py`
   - `collector128_prep/vendor/feedparser/namespaces/admin.py`

22. SHA `9e482d1b4dffdc4f08ca5a4f2c1cd032d73f4f96` (2 paths):
   - `collector112_prep/vendor/feedparser/namespaces/cc.py`
   - `collector128_prep/vendor/feedparser/namespaces/cc.py`

23. SHA `fdf4cc11fcb98f9b65e87a0b6ada64c35a803730` (2 paths):
   - `collector112_prep/vendor/feedparser/namespaces/dc.py`
   - `collector128_prep/vendor/feedparser/namespaces/dc.py`

24. SHA `2f30350686e54685d4d03c64a4dc736ca6baf884` (2 paths):
   - `collector112_prep/vendor/feedparser/namespaces/georss.py`
   - `collector128_prep/vendor/feedparser/namespaces/georss.py`

25. SHA `7cebfae9a0a157b3e6fb89f78f97818588d7102c` (2 paths):
   - `collector112_prep/vendor/feedparser/namespaces/itunes.py`
   - `collector128_prep/vendor/feedparser/namespaces/itunes.py`

26. SHA `00a07afbcbf277aba5bb3194f8cd147d47371cdd` (2 paths):
   - `collector112_prep/vendor/feedparser/namespaces/mediarss.py`
   - `collector128_prep/vendor/feedparser/namespaces/mediarss.py`

27. SHA `519bee1d8e1e6b9256f7215ded2ef16bebe06ea6` (2 paths):
   - `collector112_prep/vendor/feedparser/namespaces/psc.py`
   - `collector128_prep/vendor/feedparser/namespaces/psc.py`

28. SHA `ee0b58b1384633bd93a19495410503662ce812d1` (2 paths):
   - `collector112_prep/vendor/feedparser/parsers/loose.py`
   - `collector128_prep/vendor/feedparser/parsers/loose.py`

29. SHA `d40797a7aa9137eef646a07f4e7a756c1095c337` (2 paths):
   - `collector112_prep/vendor/feedparser/parsers/strict.py`
   - `collector128_prep/vendor/feedparser/parsers/strict.py`

30. SHA `597a72b87f373ddf1c271a6d68892c0fdc385ecd` (2 paths):
   - `collector112_prep/vendor/feedparser/sanitizer.py`
   - `collector128_prep/vendor/feedparser/sanitizer.py`

31. SHA `ae5edf2a21660fb44136ce1d2672e1641324e010` (2 paths):
   - `collector112_prep/vendor/feedparser/sgml.py`
   - `collector128_prep/vendor/feedparser/sgml.py`

32. SHA `1155f26e61cadf0ef45210169e1f7381d249e72a` (2 paths):
   - `collector112_prep/vendor/feedparser/urls.py`
   - `collector128_prep/vendor/feedparser/urls.py`

33. SHA `5ad3a84a0e40974637e123dc9df934c408ca167b` (2 paths):
   - `collector112_prep/vendor/feedparser/util.py`
   - `collector128_prep/vendor/feedparser/util.py`

34. SHA `88a02a307f4013abccb867cac97075e22acf06a5` (2 paths):
   - `collector112_prep/vendor/sgmllib.py`
   - `collector128_prep/vendor/sgmllib.py`

35. SHA `8690672cdaec0e8a9f66d56a81c1508fe4379805` (2 paths):
   - `collector114_prep/worker.py`
   - `collector124_prep/worker.py`

36. SHA `52d91a8b9cf8313185c9a1f996c83ac8569009a2` (2 paths):
   - `integration/dependabot_security173/build-output.txt`
   - `integration/pypdf_remediation105/build.log`

37. SHA `c688d8ccdad82420475fc31cb40020cccfeeef2b` (2 paths):
   - `integration/dependabot_security173/pip-check.txt`
   - `integration/security_candidate/bump158/pip-check.txt`

38. SHA `cb1c652df2794d69088f745b6cefd0d7214ef648` (2 paths):
   - `integration/finder198_ui/panel.css`
   - `integration/finder_proxy_f12/panel.css`

39. SHA `b2dd568b4449d0fe5cb38be88c048c8a86cc7311` (2 paths):
   - `integration/finder198_ui/ships226.mjs`
   - `integration/finder_proxy_f12/ships226.mjs`

40. SHA `ebdf548e67e5850a3d12359ddcbdf6c0caba7acb` (2 paths):
   - `integration/geospatial/geo_map.css`
   - `integration/ui/geo_map.css`

41. SHA `58fb3d26025c8c0b8de21739e5ae52c70cc73af0` (2 paths):
   - `integration/geospatial/map_ui.js`
   - `integration/ui/geo_map_ui.js`

42. SHA `d6b0ee61b66ba990bde35bec2b969e9f1bde991b` (2 paths):
   - `integration/geospatial/ui/map.css`
   - `integration/ui/map.css`

43. SHA `37c8c4debcb3f1bec0bad9649ae2d50e4accf874` (2 paths):
   - `integration/geospatial/ui/map.html`
   - `integration/ui/map.html`

44. SHA `9c09e357ded8096f6ab40366042c661b1b30c87f` (2 paths):
   - `integration/geospatial/ui/map.js`
   - `integration/ui/map.js`

45. SHA `bcb3ba1aca095155857556d96e3193a50fe1bd11` (2 paths):
   - `integration/public_map_m2/LICENSE`
   - `integration/public_map_prep/LICENSE`

46. SHA `2961b7618a57617d1015d31d2094c425c3d86ce9` (2 paths):
   - `integration/public_map_m2/leaflet.css`
   - `integration/public_map_prep/leaflet.css`

47. SHA `a3bf693d0fcaff885cc5f21b3a699aaa567b3533` (2 paths):
   - `integration/public_map_m2/leaflet.js`
   - `integration/public_map_prep/leaflet.js`

48. SHA `450754498abab64be55667448efd61a3c5436348` (2 paths):
   - `integration/security_candidate91/app-closure.json`
   - `integration/security_maintenance94/closure.json`

49. SHA `ff6e12d57a3df380fd9396fa9b7012afe9942f16` (2 paths):
   - `integration/security_candidate91/bootstrap-lock.txt`
   - `integration/security_maintenance94/bootstrap-lock.txt`

50. SHA `0f5e53b0532437823ccd2f3d8a66fd67e768c643` (2 paths):
   - `integration/ui/public_weekly.css`
   - `integration/ui/weekly.css`

51. SHA `635d392db334c40475df150684a84a86dabb3fd3` (2 paths):
   - `portable_validation28/evidence/receipt1.json`
   - `portable_validation28/evidence/receipt2.json`

52. SHA `678aefb9491cca7ba98fbbafc0c94d8f5d2ac205` (2 paths):
   - `runtime_build/evidence/receipt1.json`
   - `runtime_build/evidence/receipt2.json`

53. SHA `32ede3eecaf2db56602b896a4c114e9aea5acb22` (4 paths):
   - `runtime_executor27c/evidence/29a-unchanged-receipt.json`
   - `workflow_executor29b/evidence/29c-baseline/29a-preflight.json`
   - `workflow_package29/evidence/receipt1.json`
   - `workflow_package29/evidence/receipt2.json`

54. SHA `a3a42ae8b90db0078b133f575bfe74aaf3399bdd` (2 paths):
   - `runtime_executor27c/evidence/default1.json`
   - `runtime_executor27c/evidence/default2.json`

55. SHA `8a6de815663840d3efd674805d77a4302ce417f0` (2 paths):
   - `workflow_executor29b/evidence/29c-after/28a-harness.txt`
   - `workflow_executor29b/evidence/29c-baseline/28a-harness.txt`

56. SHA `6ad10f3f394d675f0f441ef5ec593b296abf3397` (2 paths):
   - `workflow_executor29b/evidence/default1.json`
   - `workflow_executor29b/evidence/default2.json`

## Safe next steps

- Run the repository audit script: `python scripts/repo_audit.py`.
- Build the Finder using Node.js 22+: `npm run check`.
- For each candidate consolidation, search references/imports and update preservation/staging manifests in the same change.
- Move only verified runtime modules in small coherent slices; keep evidence, source archives, data provenance, licenses, and public routes intact.
- Merge only after the quality/security workflows and relevant feature-level checks pass.
