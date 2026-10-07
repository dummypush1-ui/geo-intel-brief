# Collector119 supplied-fulltext outcome snapshot correction

Inactive, production OFF. Prior118 unchanged.110 capture accepts dictionary<=100
keys, so118 enabled fulltext>100 unique eligible URLs refused.119 captures the
full outcomes mapping as list-of-{url,outcome} records together with candidates,
then reconstructs a plain bounded mapping from captured records before any
per-chunk enrichment AST. No resource cap increase:2MiB,20000 nodes,depth8,
list1000,string10000 unchanged. Exact URL keys<=2000. Resource budgets can still
refuse large1000-item runs, explicitly, not falsely claim unlimited parity.

9 local tests: all prior6 enrichment cases,120 eligible candidates cross100-chunk
boundary successfully;240x10000-text input refused by same aggregate budget;
custom outcome object refused before adapter AST. Production/network/write/
article_verified False. Other real extraction/URL/isolation/backup/GNews/runtime
and source health/deployment gates unchanged. This fixes supplied-output plumbing,
not live trafilatura extraction or full-feature readiness.
