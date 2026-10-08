# NITI / India government open-data backend review candidate
Copyright (c) 2026 Push. All rights reserved (new code only).

Pinned base: 739107f95affa02d828e72005991586025278538.
New files only. No original entrypoints, features, workflows, metadata manifests,
credentials, Render service or databases changed. Police track was dropped.

## Ready for code review, not live data readiness
- Strict bounded CSV/JSON imports with exact reviewed column mappings.
- NDAP exported snapshots supported. No invented NDAP API or dataset IDs.
- Optional injected export pull and OGD resource pagination; disabled by default.
- Standard-library HTTPS transport: verified TLS, pinned public DNS address,
  no redirects/cookies/proxy-environment/retries, sanitized errors, size limits.
- Canonical observations: original metric/unit/period/geography, decimal value,
  stable identity, source date, payload hash, publisher/source/rights provenance.
  Missing values are not zero; unknown dataset dates do not become fresh now.
- Atomic supplied-map snapshot candidate and read interface. Data stays in its
  own dataset layer, never coerced into article schemas or overwriting news.
- Separate proposed storage resource contract, no client creation, Mongo
  writes, index creation, TTL, deletion or route registration.

## What remains before live use
A verified dataset export/OGD resource, real headers/units/dimensions, permitted
reuse/required attribution and provider limits. Operator must provide exact new
collection mapping, transactional store adapter, non-public server credential
handling and mount into the reviewed app. No source has been called by this
backend, and no real NDAP dataset fixture or authenticated API smoke was run.
Unknown numeric quotas and API availability are not success claims. The strict
OGD shape may reject a legitimate dataset with different response metadata;
review its actual schema rather than loosening validators blindly.

NDAP exports requiring browser login, expiring signed URLs or non-CSV/JSON
formats must be downloaded through an approved route and passed as bytes.
This transport does not automate accounts/login, use undocumented NDAP APIs,
follow cross-host redirects or parse PDF indicator tables.

Only a complete validated nonempty snapshot may stage replacement. Failed,
partial, held and disabled pulls retain the old supplied snapshot. An empty
source is held, not treated as deletion authority. A published numeric change
updates a stable observation key; a duplicate/underspecified identity holds the
whole batch. No automatic merging of changed district boundaries or LGD codes.
Caller must include additional dimensions in metric/row-id mapping where needed.

## Example offline use (fixture, not real government facts)
```python
from integration.india_open_data.core import source_spec, import_export, stage_snapshot
from integration.india_open_data.data_layer import GovernmentDataReader
spec = source_spec(
    dataset_id='niti_reviewed_export', publisher='NITI Aayog',
    source_url='https://ndap.niti.gov.in/', provider='ndap_export',
    dataset_date=None, coverage='Explicit coverage from actual dataset',
    columns={'metric':'Indicator', 'value':'Value', 'unit':'Unit',
             'state':'State', 'district':'District', 'period':'Year'},
    license_url='https://ndap.niti.gov.in/', reuse_reviewed=False)
# Actual bytes/headers and rights review still required; URLs above are portal
# placeholders only, never claimed to be verified dataset/license permalinks.
records = import_export(b'Indicator,Value,Unit,State,District,Year\nDemo,1,count,TN,Demo,2021\n', 'csv', spec)
snapshot = stage_snapshot({'state':'complete','records':records}, {},
                          'niti_reviewed_export', '2026-10-08T23:00:00+05:30')
view = GovernmentDataReader(snapshot).read('niti_reviewed_export', limit=100)
```
Rendering/display of untrusted imported text must use the existing HTML escaping
and CSV formula guards. The module returns data, not safe HTML/CSV cells.

## Review test command
From repository root:
`python3 -m unittest discover -s tests/india_open_data -v`
All tests are synthetic/offline. No visual deliverable/UI changes.
No full application regression, dependency inventory refresh or preservation
manifest changes included. Builder must perform those after integrating additions.
Socket timeout is per operation; production worker needs total-runtime cap.
Pagination cannot prove snapshot isolation if provider changes rows mid-pull;
prefer published static exports or dataset-version verification for live use.

## Accepted fail-closed limits
Control characters are a hard failure in labels and source specification text.
In particular, multiline CSV labels with embedded newlines/tabs are refused,
not silently flattened or altered. Duplicate observation identity rejects the
entire dataset, even if duplicate numeric values agree.
GovernmentDataReader's 10,000-row cap applies across ALL datasets in its supplied
snapshot map, not 10,000 rows per dataset.
DNS getaddrinfo has no timeout; socket timeouts do not bound DNS resolution or
total wall-clock duration. Every live pull must run in a bounded worker with an
external overall deadline and termination/reaping on timeout.

The additive landing delta accompanies this bundle. It describes new paths,
AST/import/hash entries only. It is not a replacement for the repository's
existing preservation/staging/import audit manifests or their landing gates.
