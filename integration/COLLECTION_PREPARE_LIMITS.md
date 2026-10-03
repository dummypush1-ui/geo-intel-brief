# Offline collection processing seam

This seam accepts ordinary plain deserialized JSON-like candidate dictionaries.
It is not an interface for arbitrary Python objects: deep copying such objects
can run their custom code. The 1000-row bound does not bound individual string
length or fuzzy-comparison CPU/memory use. Keep fixtures reasonably sized.

Geo classification precedes dedupe and category filtering. The original stored
summary preview is limited to 300 characters. BRICS dedupe precedes category
classification/filtering and BRICS relevance filtering. BRICS processing rules
are a copied snapshot of preserved originals and can drift from future changes.

This establishes processing-order/rule parity against archived originals, not
live production parity or a full collector migration. Geo's unused dateutil
parse_date helper is not called by this adapter. For filesystem-free probes,
run with -B/PYTHONDONTWRITEBYTECODE=1 to avoid Python bytecode-cache writes.

Inputs are copied, including supplied identity/time fields. No collection time,
writer identity or stored status is invented. Fetching, store connections,
inserted-count versus inserted-item semantics, URL IDs, timestamp assignment,
duplicate/storage-error handling, alerts and Telegram backups remain outside
this seam. No API, scheduler, runtime, fetching or persistence is enabled.
