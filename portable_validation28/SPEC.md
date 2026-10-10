# 28a SPEC + local harness only

LOCAL CPython3.10.12 Linuxx86_64 only. 28 remains OPEN. No existing tests fixed, no production policy changed. No target/ABI/Render/512MB/runtime-ready claim. CP312 execution NOT RUN, cannot be substituted by declared marker fixtures. 27b ownCP312sgmlwheelanchor awaits capableexecutor, remains separate queueddependency.

Source baseline8e7f5a6f11bd7ac497de73ce13156132990af3b2. Inert portable_validation28 additions only. Root/workflow/requirements/27a/27b bytes unchanged. source-allowlist hashes all existing files read for findings; drift fails. Existing27a verifier also rechecks its exactartifactinputset/sourceallowlist before local freshvenvs. No new pins, packageinstall only existingreviewed offlinehashed27aprofileinsideisolatedscratch. Artifactbytesnotrepo.

## Findings, not fixes

- tests/geospatial/test_map_route.py:70 creates '['*2000+'0'+']'*2000 and asserts rows=[], status.ok=False, reason='unreadable'. integration/geospatial/response.py:26 calls json.loads and at29 catches OSError/ValueError/RecursionError. Thus the assertion depends on whether depth2000 raises in the chosen interpreter. Current3.10.12recursionlimitmetadata1000; observationrowrecordsactualjson.loads outcome. This is SKIP, notpass/fixed. NoassumedCP312threshold.
- tests/test_dependency_audit.py calls Requirement.marker.evaluate({'extra':''}) for active/inactive historicalauditdependencies, leaving otherkeysambient. 28a independenttable suppliesall12markerkeys. Historicalaudit/lockbytes unchanged.
- tests/weekly_report/test_report.py imports pypdf in pdf_text/page/linktests; externalvalidator at404 importsoptionalpikepdf, skipsifabsent, otherwisecalls pdf.check(). 28a pypdf6.19.0 strictreaderopens generatedharmlessblank1page+checksmetadata. NOTequivalenttopikepdf.pdf.check(). pikepdf optional absent BLOCKED, notpass. No dependency added.
- tests/test_schedule_caller214.py defaults Asia/Calcutta; canonicalAsia/Kolkata usedelsewhere. Zoneinfoequivalence tested aroundfixed18:30UTCdateboundary, nofallbackorcreatedalias.
- collector110_prep/input_budget.py production MAX_DEPTH=8 unchanged. FIXTURE_DEPTH_PROBE=64 is harness-only nestedarraylanguageprobe, NOT generalJSONvalidator or newpolicy. Iterative strings63/64/65 give accepted/accepted/refusedfixture_depth_probe. NoRecursionErrortextassertion.

## Matrix and evidence

Every rowstatus oneofPASS/FAIL/SKIP/BLOCKED/NOT RUN withreason+actualinterpreteridentity. Countskipseparately. 3.12markerrows evaluate declaredfixtures on3.10, clearly NOTPython3.12 execution. Independentliteralexpectedtablehasbothversiondirections; current3.10versusdeclared3.12 switchprovesdeclareddrivesresult.

Zoneinfo resolvesbothrealkeys +05:30/samedatesat4fixedinstants. Requiredaliasabsent->BLOCKED noUTCfallback. Metadata systemtzdata.zi version/header +zonefilehashes. Existingbwrappatterndoesnotmounthostdpkgdatabase; tzdatapackagequeryunavailableisrecordedBLOCKEDmetadata, notinventedversion. Hostoutside-sandboxobservedtzdata2025b-0ubuntu0.22.04.1/system2025b, cacheorientationonly, notproofinsidecontainer.

Bwrap unshare-all RO/usr/lib/lib64+proc/dev, scratchonly, nohome/downloads; externalconnectrefused. HarnesscreatesONLYownharmlesssleepchild, subreaper, hardchildpid2secondtimeout, killsprocessgroupandwaitsleader+descendant, checksPIDsabsent. RLIMIT1GiB addressspace/CPU/filelimits PERPROCESS, NOTcombined512MBtarget. NoOOMstress. Noappserver/collector/provider/DB/userdata/mail.

Twofreshhashedvenvssemanticreceiptsbyteidentical; timestamps/absolutehostpaths excluded. Recursionlimit onlymetadata, PID/timeexcluded. Noenvironment-wide/venv/pycreproducibilityclaim. Negativeprobesdeclaredenvs/depth/tzabsence/skipnotpass/sourcedrift. Fulloldrootgatecountsremainhistorical, not28aevidence.

Harnessinitialattempts failed: /bin/sleep notmounted (corrected/usr/bin/sleep); hostdpkgpackageDBnotmounted (now metadataunavailable); testexpected11keys buttablehas12keys corrected. Discardedattemptvenvs, fresh2completepassrunslogged. Nooriginalcodefixes/dependenciesadded.

Remaining28b actualtestfixes requireseparatecontract/editallowlist+pinreview. CP312/realcandidateimagevalidator/bwrap/deadline/reap/combined512MBacceptanceUNRUN. Gunicorn22vs23,bcrypt5,extras,nativeprivateinternals,historicalwheelopen.27/28/29open.

Re-run (sameinterpreter,bwrap and exact27aartifacts supplied separately):

    python3 portable_validation28/run_local.py /path/to/baseline-with-overlay /tmp/28a-clean /path/to/exact27a-artifacts
    python3 portable_validation28/test_harness.py

Runner requiresfreshnonexistentworkdir. Tests import onlyinactiveharness. No workflow/import by existing app.

Run the harness ONLY through run_local.py. Its sandbox-only assertions deliberately fail elsewhere. 28 remains OPEN; 28b actual fixes need a separate contract and pin review.
