# Offline dependency audit: candidate blocked, not an installable lock

Scope CPython3.10.12/Linuxx86_64, static integration/tests/scripts AST inventory,
minimum staging+discovered unittest+original pure AST fixture support. Original
requirements-staging and Geo/BRICS requirements unchanged. Configuredvenv unchanged.
Inventory records installedmetadata import->distribution mappings and direct/
transitiveRequires-Dist with active/default-extra markers. Standard/local/unknown
imports and dynamicimport files retained, static discovery NOTcomplete runtime
proof. Intentionally excludesmanualPlaywrightbrowser scripts/binaries; noimport
of arbitrarypackages merelytoidentifyversions. Node22.23.3 separatetestprerequisite.

25distribution closure audited,24compatiblewheels inexplicit/downloads/wheels68.
Exactfilename/version/tags/SHA256 in audit.json. sgmllib3k1.0.0 hasonlysdist present,
SHA256 recorded, inspectedsetup.py importssetuptools/readsREADME; noofflinebuild
performed and no wheel hash fabricated. Noambientindex/cache, latest/no-deps/pin
loosening. requirements-offline-reviewed.candidate.txt deliberatelylabelledNOT
INSTALLABLE hashedclosure because missingwheel/hash. It is NOT environment-frozen
proof, a productionlock or freshinstallclaim. Cachefiles privateworkspace/local,
notpublisheddependencybundle or promiseduser-accessibleartifact.

Separate outcome statuses:artifactclosureBLOCKED; offlineinstall/importsmoke/
freshSDKbackendchecks/freshsuite NOTATTEMPTED. Configuredsuite regression evidence
only. Anewvenv sharesbaseCPython/Expat, not reproducesOS/interpreter. 85 requires
feedparser6.0.11plus32SDKsourcehashes, sgmllibsourcehash andExpat2.4.7; matchingwheel
versionsalone insufficient. ExistingSDKpins in integration/feedparser_audit and
resourcechild verify them locally, NOTfreshenvverified. No OSnetworkisolation.

Optional pikepdf missing ->weekly_report.test_report.Writer.test_external_validators
skip. trafilatura absent separatelypreserves unavailable-provider baseline, notPDF
skip. Neither added silently. Xfailaccounts.test_reservation_terminal.ReservationTests.
test_UNSUPPORTED_two_limiter_compensation_marker_interleaving remainsunfixed, not
passproof. ManualPlaywright1.48/greenlet3.1.1/pyee12/browsers excludedminimumlock.

INERT futureinstructions ONLY AFTERcompatiblemissingwheelclosure is suppliedand
allhashesvalidated, neveragainst configuredvenv:
1. Createanewdisposablevenv with matchingCPython/OS/Expat baseline.
2. Install completeapprovedhashedlock using pip --no-index --find-links <explicit
   verifiedartifactdirectory> --require-hashes -r <completehashedlock>.
3. Verify transitiveclosure/pipcheck, importonlyreviewedpuremodules, SDKphysicalpins
   andbackend, thenfullconfiguredtests includingNodeprerequisite.
DoNOTrun currentcandidateascomplete. Noexternalpipfetchauthorized orneededforaudit.
Eachfuture subprocesswall/outputmustbound,kill/reap; importmonkeypatchnotOSfirewall.
No productioncollector/configimport/liveRender/DB/credentials/deploy/readinessclaim.

Auditjson environment/sourceinventory is localcontext, notsecrets. Tests verify
hashes/cacheclosure/version/markers forrecordedcandidate; noactivation sideeffects.

Revision87 review correction: inventory is bound to revision86
4d7f7f342140a144f429d03f82b94a3176f341c2, with all263 scoped Python paths and
SHA256s. Scanpolicy/exclusions recorded; currentfiles checkedagainst baseline.
Eachimport is classified stdlib/local/required_distribution/optional_absent/
excluded/unresolved. Metadatafilepaths resolve flask/werkzeug/bson/pymongo/pypdf
where packages_distributions omitted them. Provenance retained; unresolved=[]
for this static scope only, not runtime completeness. Namespace/local paths
are recorded, not inferred dependency absence.
Seven focusedchecks cover activeclosure/specifiers/markers, canonicalunique
names, exactperdistributionlockhash equality, wheelbytes/tags/METADATAincluding
activeRequiresDist, completeclassifications and baselinefilehash/ASTconsistency.
Unavailablecache is an explicit UNVERIFIED unittestskip, never hashverification
success; authorcacheavailable and all24 wheelbytechecks pass. Independentreview
hasnocachebytes unless transferred. No freshinstall/importclaim added.
