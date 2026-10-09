# Item11 pure selection preparation, ONE digest

Original owner menu11:18 on2026-10-09 offered24h/7days/all-time withoutrepeat;
owner11:19answered1 2 3. Mainclarified taskshape: one24h+7dsectiondigest with
all-time displayed receipt exclusion. No three modes or all-time article section.

Source plan only, not UI/render/query/store/send/mark/scheduler. Explicit caller
published OR created_at policy, with no default: owner has notpicked whichdate.
Pure plans leave raw_mongo_query=None because zoned stringdates sortlexically,
notalwayschronologically. No naïve$gte stringdatequery or schema migration.
Dates interpreted normalizedUTC,inclusive start/end,futureexcluded. Section7days
includes24hbydefinition; overlap reported, uniondisplayedIDs dedup internalonly.
Cap60persection AFTERscore>=4 differs fromoriginalcap-before-score-filter; only
showneligible IDs proposed for future receipttracking, no actualmarkpermission.

Exact1000row/2MB/16ktext fixturebound, uniqueObjectId, fullinputvalidationbefore
filter/exclude. SelectscoreDESC/normalizedpublishedDESC/ObjectIdDESC. All-time
per-channel injected exactObjectId tuples≤10000modeldisplayedreceiptexclusions;
notauthenticateddeliveryorcompleteledgerproof. Legacyemailed bool isnotchannel
receipt, intentionallyignored (reported). Noall-time receipt truncation: reject
oversized input, futuredurablestore lookup required. Snapshot hash bindsinput,
clock/date/channel/receiptsets/limits, notDBsnapshot/no-repeat/sendproof.

Remaining: ownerdatepolicy, overlappingdisplaydecision, renderer/windowlabels,
actualsource fullschema/normalizeddatequery,indexexplain, durablecrossworker
claim/receipt and all-timeidlookup keyedbychannel, events-onlybehavior, optional
limitdecision,timezonesandexactsendtimes, authenticatedsendack/markrecovery.
Currentlegacyholdsremain; this cannot activate mail or promise repeats prevented.
No renderer/UI/pixels changed; noevents falselycountedzero. No source read/network.
