# Selected design: AppsScript + free Render web, inactive

Original keepAlive source confirmed live main unchanged October7,2026:
f23159b30f263e3a34cae29879900d73b23f6cf64fc6958f12712b7df484026a.
It hits OLD RENDER_BASE_URL/health with old querysecret. New additive ping must
hit separate collectionbase; old mail/base/triggers remain unchanged. No global
setupTriggers invocation (deletes ALL triggers). Active10min successfulHTTP
preventsordinary15minidle, but not restart/crash/monthlyworkspace750h quota.
Two continuouslyawake freeweb services exceed750h/month sharedworkspace;
check actualservices/remainingquota before asserting viable monthlycapacity.

Freeweb job lifecycle should use request-driven bounded work slices. Acceptance
HTTP202 alone doesnotspawn durable work. Add authenticated drive/status poll by
AppsScript; persist onephase at a time using majorityjournaled Mongo CAS ledger.
No RAMdaemon as sourceoftruth. Transport/budgets and fixed originalpreparation
mustfinish before adapter executes anything live. Jobstorecollection/role is a
newpermission gate, not smuggledinto existing geo_readonly client.

Current CAS ledger is injected and creates no client/index. Profile document
serializes jobs and fencing increments. Replay/history max64: failsclosed when
full until separatelyreviewed archival mechanism. Exact fingerprint required.
Expired lease NEVERstolen: crashes beforewrites block until safeprocessdeath
and checkpoint reconciliation. Uncertainwrite profile latches. Real article
writes are not fence-aware, so leaseexpiry cannotautomatically permitoverlap.
Ledger majority+journal validation notimplemented yet. Do not call complete.

Remaining recovery design: durable checkpoints; processidentity/readback;
prewrite candidates safe restart; write-start articleURL+runreceiptreadback;
transaction or no-takeover serialization; reconcile unknownbeforeunlock.
Cannot promise every missed cycle iscovered automatically while preserving
bounded lookback/unknownpartialwrites. Separateexplicitlivecutover required.
