# Separate private manual sample-check app, offline only

create_probe_app explicittrustedconfig only. No env/readstandardlauncher import,
route addition to main app, proxytrustselection/deploy/sourcegrant. Reuses single
workerPreviewAccess/login, secureHostcookie/origin/twohour authentication, csrf
forprobePOST. AuthouterWSGI beforedispatchunknownpaths/methods. POSTexactOrigin,
urlencodedonly, singlecsrf/noextras/noquery. Allstatusesprivate/no-store/noindex/
nosniff/defaultdenyCSP. FormonlyGET; responsefixedsmallJSON. Noautomaticfetch.

ModuleglobalnonblockingLock and10minattemptcooldown acrossappinstances; failures
consumecooldown, noqueue/retry/polling. Stateperprocess/resetonrestart, notdurable
or distributed. OneGunicornworkerrequired. NoDBstatus exposed withoutlogin.

FixedexecPythonmodule child, minimalGEO_MONGODB_URI+LANGenv, noURIargv/shell/fullenv.
Child loggingdisabled,stderrDEVNULL, popsURIenv beforeprobe, emits fixed result.
Secretremainschildmemory duringoperation and initiallyprocessenv; authorizedOS
inspection is not isolated. StartupPython/libraryerrors could depend on platform;
no blanketplatformloggingcertificate. Trustedrunnernotuntrustedexecutableinput.
Parentselectors reads<=4096byteUTF8strictresultschema;10secondbudget, timeout or
malformed/nonzeroresult=>fixedunavailable. Kill/wait/close onnormal/error/control.
Clientownedchild; nochildren expectedfromfixedcode. Parentkill targetschildonly,
notarbitrarydescendantprocesses. Childmustnothostuntrustedplugins/hookspawners.

10s clock/select/read/poll budget isn't finitewholeHTTP/ingressdeadline orhard
processspawnbound. kill/waitcleanup canitselfstall atOSlevel; no guaranteed10s
requestcompletion. Clientdisconnectdoesnotinterrupt synchronousWSGIexecutor;
childnormallyfinishes/timeouts, thenlockreleased. Actualnetworkslowclient/
disconnect/Renderproxy tests notyetperformed. GUNICORN timeoutmustnotbeclaimed
asrequestcancel+childcleanup proof. Parentworkerforcedkill could orphanchild;
hostactivationrequireslifecycleproof orstrongerprocessgroup/watchdogdesign.

15nativeofflineHTTP/process tests:authpathmethods/loginCSRF/origin/query/type,
fixedresponses/crossinstancecooldown/busy/controlrelease/importinert,realexec
success/malformed>4096/nonzero/stderrdiscard/immediateclocktimeout/childkillwait,
strictschema/invalidURI/childenvpop. Timedtest usesforcedclockadvance, not10real
secondnetworkhang. NoMongo/Render probe executed. Standard gates untouched.
Needindependentreview,fullsuite and visualformcheck beforebackup. Noactivation.

V2 auth hardening: PreviewAccess now import-light (news_api imported only when
build/from_env called), one nonblocking global-peraccess hashslot plus atomic
attemptreservation beforehash, including successfullogin attempts. No24thread
expensivehashfanout. ExactOrigin nowrequiredlogin/logout/probePOST, logoutcsrf
issuedatlogin. UTF8bytecomparison rejectsnonASCIIinvalidCSRF403,notTypeError500.
Existinglogin/logoutbehavior changedintentionally forsecurity; noDB/readgate
change. Logoutcallers needcsrfparameter fromsession, notbarePOST.
URIstillininitialchildprocessenv, notOSsecretisolation. killchildonly, notprocess
groupcleanup. InitialHTTPreviewUNSAFE supersededonlyafterfreshreview; noreadiness
claim. 12access+15wrapper/process nativefocused tests planned/rerun.

V3 sessionrevocation: bounded128active server-side nonces perPreviewAccess,
expiry2h, purgeonlogin/authorize, logoutremovesnonce; replayedprevioussignedcookie
refused. Restartrevokesall sessions. Singleworker/peraccess stateonly, notshared
productionaccounts. Loginreplacesoldsessionnonce. Capacityfailclosed429, noeviction.
Browserlogoutformdeliveredon/db-check and/private-session; HTTPonlytests take
hiddenCSRF and replayoldcookie, notsession_transaction backdoor.
Canonicaloriginstartupvalidation rejectsports(including443), uppercase,backslash,
credentials,path/query/fragment and malformedhost. SimplelowercaseDNSnames only.
Oversizedpassword400 beforehashreservation. Busy429 consumesnoattempt. Validform
unauthenticatedcallers canburnglobal10/300s budget; availabilitytradeoff remains,
needexternalratecontrolbeforepublicexposure. Successfulhashalso consumesbudget.

ReviewV3SAFEprivate/singleworker/manualscope. Reviewer21of23HTTP/access testsPASS;
2failedonlybecauseUIassetsabsentfromincrementzip. Author42focusedwithassetsPASS,
944fullsuitePASS1skip1expectedfailure. Residuals: unauthenticatedglobalbudgetburn
needsexternalratecontrolbeforeexposure;128activecapcanlockoutuntilsessionexpiry/
logout/restart; logoutdoesnotcancelalreadyaccepted in-flightprobe; sessionexpiry
useswallclock; clockchangescanaffectvalidity; formMAX_CONTENT_LENGTH1024 means
urlencodedpassword/CSRFnear1024charscan413beforeexplicitlengthcheck. Process-local
sessions/cooldown resetonrestart, notdurable/sharedproductionaccountstate.
