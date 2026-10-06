# PRE-IMPLEMENTATION PLANNING NOTES - historical, not currentstatus

# Dependency review October6 2026

Exact25candidateapp+2bootstrapOSVquery yields8distinctapp advisories across
Flask/Werkzeug/requests/dotenv, plus11distinctbootstrap pip/setuptools.
AliasPYSEC records reconciled, no pagination. CurrentMongo/PDFplusretained
other21app packages no OSV matchingrecord, notabsenceofunknownvulnerabilities.

Proposed researchedupdates: Flask3.1.3, Werkzeug3.1.9, requests2.34.2,
python-dotenv1.2.4; exactcurrentPyPImetadata compatiblePython3.10 and retained
closuredefaultdependencies. Proposed separatebootstrap pip26.2.1/setuptools84.
No download/install/selectionyet; independentplanreviewpending. RuntimeAPI/
sourceparity and completecandidate regression stillrequired. Originalsource/
87/88/90historicalreceiptlocks untouched.

FlasksessioncacheVaryCookie: currentpreviewprivateNoStore mitigation, session
getpaths used, no blanketprotectionclaim. WerkzeugWindowsdevicepath issues
notLinuxpathproof; crossplatform .safe_join API stillneedsupstreamcontract.
Requestsnetrc+tempzip: sourcecollectors use requests.get onconfiguredfeeds,
no trust_env=False explicit; exactrelevance requires hostnetrc/tempzipconfig,
unknownratherthanabsent. Dotenvonlyload_dotenv usage found, set_key notused.
Bootstrapadvisories matterinstaller/buildinputs notsameasappHTTPexposure.
Verifiedofficialartifactintegrity+wheelonlyhashpins reducebutnoteliminate
installerissues, and are not substitutedforupdates. No credentialvaluesused.

Source ledger and exactOSV records retained separately. Beforeselection:
inspectwheelpaths/METADATA/RequiresPython/defaultclosure/hashes, independent
review, boundedsyntheticcases, fullconfiguredcandidate tests without skips,
productionpins nevereditedwithoutfinalevidence.


Currentstate: artifact/actualclosureverified and tested; independentSAFE unselectedevidencereviewOct6 22:29. See README/receipt. No pinselection.
