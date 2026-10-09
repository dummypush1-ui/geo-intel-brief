# Whole-store browse index candidates, source only

Four proposed indexes match185 raw sorts exactly: created_at/_id descending,
title/_id ascending(existing181name reused),country/_id ascending,
score/_id descending.181score/published/_id does not provide score/_id ordering
when published is unconstrained;181created_at lacks _id tie. These plans change
no read query/order/filters, no index drop/TTL and no collection/event calls.

init_db defaults provision_browse_indexes=False, separate from181query gate.
Both gates require literal booleans before connect; default retains four legacy
calls. Both true deduplicates shared title name,9newunique candidates pluslegacy.
No production caller sets either gate. Source gate is not permission to provision.

Tests compare candidate order to185source AST, mockedcreate_index contracts,
boolean defaults/dedup and explicitly synthetic explain shapes. These are NOT
real explain output, a Mongo planner, index utilization or performance evidence.
No DB contacted/index created bytests. No guarantee efficient filtering:185uses
find({},projection),rawsort then Python filtering; filtered scans may remainlarge.
No covered-read claim: article fields requireFETCH. No snapshot/count claim.

Before any separate owner-reviewed live provision: inspect actual schema/types,
collation, existing indexnames/keys/conflicts,storagecosts and real explain
executionStats for every sort and filter,includingSORTstages/keys/docs examined.
Review deployment/routing/cursor lifetime separately. No Atlas changes here.

Current source references verified2026-10-09:
https://www.mongodb.com/docs/manual/tutorial/sort-results-with-indexes/
https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/
Sort fields must follow index order/directions(or wholeinverse);non-prefix
subsets require equality on precedingfields. Source plans aren'tlive evidence.
