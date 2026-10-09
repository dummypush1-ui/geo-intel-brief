# 214: pure Geo occurrence caller, not a scheduler installation

arm/tick/acknowledge_occurrence integrate actual205next-occurrence calculation
with plain supplied state. No job is dispatched. No timer, callback, sleep,
environment, processTZ, DB, ledger, SMTP, AppsScript trigger or production mount
exists. Native/runtimeengine stays unchanged. No current module imports214except
its test. AppsScript rail and legacy schedules remain untouched. Item25 staysOPEN.

## Scope

205is Geo-only: profile_plan('geo',settings), one next occurrence per call and
ONE configured wall-time per day.214accepts ONLY exactGEO_SCHEDULER_TIMEZONE,
GEO_WEEKLY_REPORT_DAY,GEO_DAILY_RUN_TIME settings. BRICS' two collector intervals
and multipleDIGEST_TIMES are NOTcovered. Geo weeklycadence is an explicit policy
choice, not legacy installation or feature parity. No invalidweekdayMonday
fallback. Missing timezone/time/day/DSTpolicies refuses, never inferreddefaults.

OFF arm returns staticdisabled/send_allowedFalse/dispatch_allowedFalse/
activationFalse/scope before touching anyargument or importing205. Enabled must
be exactbool. ON calls175validation and205separately for exactdistinctdaily/weekly
cadences(max2), strict exactUTCdatetime anchor, explicitfirst/second/refuse fold
policy andskip/refuse gap policy. It stores at most ONEpending occurrence per
cadence, no missed-run backlog.205none_in_window is held_no_occurrence, NOTwaiting.

## State and identity

State is exactplainJSON, no datetime/callable/capability. It includes schema1,
profilegeo, settings/hash, sortedcadences, bothpolicies, last_seen, per-cadence
anchors andoccurrences. Eachoccurrence includes205evidence:UTC,localoffsetwalltime,
fold,offsetseconds,weekday,skipped_nonexistent count andexacttzdataprovenance
source/systemversion/packageversion/zonefileSHA. CanonicalJSONhash binds profile,
cadence,settingshash,anchor,ALLEVIDENCE(includingskippedgaps),bothpolicies. No
ambiguous delimiterjoin. Different folds/policies/cadences have differentIDs.

Each tick recomputes205from the STOREDANCHOR, revalidates settingshash and requires
ALLEVIDENCE/identity/flags equal. ChangedUTC/local/fold/offset/tzdataversions/source/
zonehash/policies/extra fields holds with fixedreason, no settings/errorvalueecho.
Boolean-vs-int andsubclass differences refuse. Shapes/depth/nodecounts/text/int
bounds hold beforecopy/hash. No private error context/cause remains. This checks
consistency, NOTauthentication: a caller can fabricate an entirely self-consistent
state. Such supplied state cannot authorize dispatch or prove durableacknowledgment.

## Polling and observation acknowledgement

tick takes exactUTCnow andexplicitexactint max_lateness_seconds0..3600 (bool
refused). Before occurrenceUTC=waiting; exactlydue=due; due+limit inclusive=due;
one secondlater=missed_held. now earlier than storedlast_seen is clock_rollback.
Input never mutates: only RETURNEDstate advances last_seen. Repeatedpoll gives
sameID/status, NOTa renewedjob/sendpermit. No automaticcatch-up or advancing past
unresolveddue. A poll dayslate returns ONE missed_held per cadence, no backfill
flood. Daily+weeklycoincident returnsBOTH with distinctIDs, coincidentTrue andfixed
notedispatch_not_allowed, never deduplicatedsilently.

Everyreturnedoccurrence has static send_allowedFalse,dispatch_allowedFalse,
activationFalse andscope supplied_schedule_state_not_durable_or_execution_authority.
Due means only preparation for futureexplicitreviewedcaller, neverpermission.

acknowledge_occurrence is PUREOBSERVATIONacknowledgment, notdurablejob/sendreceipt.
It requires an exactpendingID and recomputes current205evidence beforeadvancing
onlythatcadence. Next205anchor is the ACKNOWLEDGEDOCCURRENCE'SUTC, strictlyafter,
NEVER now. Lateackcannot silentlyskip interveningoccurrences. It leaveslast_seen
unchanged anddoesnotcalltransport/store/operator. Caller owns anyprovenance,
persistence andauthority; functiongrantsnone. No ack ofnone_in_window. StaleID
refuses. It is not a replayjournal/exactlyonceguarantee.

IMPORTANT: acknowledge_occurrence has NO CLOCK. It accepts a still-WAITING
(not-due) pendingID and advances it, silently skipping that day if misused. A
future TRUSTED caller may only acknowledge IDs it actually observed in a due or
missed_held tick result. This unit does not enforce that evidence or authority.
Every tick re-reads205tzdata; source/package/zone changes hold(changed), never
automatically re-arm. A future explicit reviewed re-arm path is required.

Supplied-state dedup NOTexactly-once. Crashed/restartedprocess loses
acknowledgment unless futuredurablecaller persistsit; it may repeatobservation.
Nothing about duplicateIDs guarantees no duplicatecollector/mailjobs. Activation
needs durableoccurrenceclaim/checkpoint, clock/restart/missedrunpolicy,
source-groundedowner timing/cadence/DSTchoice, reviewedtimer/callback,
weeklyidentity, actualdeploymenttzdata andAppsScriptcutover. Native201c held.

## Grounding and tests

Actualcurrentmain205live-readSHA25644fd51c027e14bef4c30cf81b4fd4bf77d1faac1637b6b414fbeaa6c88f8ee52
matchedlocalbase. ActualoriginalGeo schedulerdc42e6147db678d3ad93d62f3412cd521230a040296a405e60d77588b99936a0
uses process-local schedule.every().day.at, weeklyMondayfallback and--now.
BRICSscheduler8e57b8aa7aeed25d4b9723d5235861b8f4be38c336de6be79e32bc713ba63f26
usescollectorintervals/multipleDIGEST_TIMES, no weeklyinstall. Both readlive,
neitherimported/executed. Legacyinit_db outageguard remainsseparate, notsilently
"fixed" by this caller; no legacycollectorentry is invoked.

11newtests+205/175=30focused: realdaily/weeklyIST/equality/latenessboundaries,
rollback/deepcopy, dayslateheldoneeach/ackanchoroccurrence-not-now, coincident,
NYfold0/1/gaps/skippedcount/policyIDs/LordHowe, mutateEVERYstoredoccurrenceleaf,
statefields/subclasses/boolint/extra/configmissing/naive/nonUTCnow, tzdatadrift,
none_in_windowheld, OFFhostileargs/importtrap/sysmodulesunchanged, duplicatepoll,
JSONroundtrip/staticflags andASTallowedimports/no currentactivationedge. Expected
timevalues depend onlocal205tzdata, notverifiedproductiondata. No live scheduling,
mail/DB/collector/timer/trigger/cutovereffects occurred.
