# Candidate27b incomplete source draft

candidate image target chosen by runtime and reviewer for build-input closure

fetched-and-hashed CP312/deb candidate inputs, byte-compared 11 Python module sources; build not run; no install, import, ABI, closure or target-solver proof.

PathA: Ubuntu24.04 linux/amd64 aptCPython3.12. PathB not evaluated. HostworkflowUbuntu24.04 is not proof of containerOS. NoRender target claim.27/28OPEN;29advancesinputclosureonly.

Registry digests: observed from the registry's own responses and re-observed by two parties. Tag 24.04 is mutable, discovery only. Observed at 2026-10-10, not a claim of what the tag points to later.

Apt metadata: signature-valid against a keyring SUPPLIED from the workspace, not independently authenticated. Fingerprint matches a public Ubuntu-hosted mailing-list page - corroboration, not a trust bootstrap. Reviewer's gpgv run used the same supplied keyring, so it adds reproducibility but no new authentication. The Dockerfile's apt trust path (keyring package or key file) must be pinned by hash in the inputs and named as such.

noble InRelease dates 25 Apr 2024 (release pocket); updates/security 8 Oct 2026. Snapshot id 20261009T000000Z is the single pin for all three. Record that pocket dates differ. Apt behaviour with snapshot URL + these suites must be fixed in apt.sources; the apt.sources hash is what build-args.REVIEWED_APT_SOURCES_SHA256 carries.

The deb closure is a local apt_pkg metadata traversal, NOT an apt/dpkg solve against the target image. It does not prove installability or closure. Never say "closure verified".

## Refusal state

inputs/application.pending.lock deliberately excludes sgml wheel pin. inputs/application.lock is ABSENT. OwnCP3122builds/outputanchor pending capableexecutor. Existingworkflow required-filecheck MUSTfailmissingapplication.lock. Dockerfile also refusesmissingreadylock BEFOREapt/network. No guessed27a wheelhash reused. Neednewreview beforeaddingreadylock orlocalbuiltwheel fetchroute. This is not a workflowreadybundle or executablebuild plan.

Exactmanifest covers allruntime_buildfilesincludinghistorical27a additions; excludesonlyinputs-manifest.json+inputs.sha256 perworkflow. Historical27a change-manifest/README/evidence bytes untouched anddo notcover27bnewfiles. Newchange-manifest27b.jsoncoversonly27badditions excludingitselfandanchorfiles (listedseparatelyreceipt). Rootmetadata/locks/requirements/.githubuntouched.

## Apt approach

Use apt signed snapshot sources ONLY, roots explicitpkg=version. apt --simulate chooses actualbase-dependent plan, rejectsremoval/unlistedversion/downgrade; download-only apt checks signedindexhashes. Explicitdpkg-deb package/version/arch+size/SHAchecksagainstledger before apt --no-downloadinstallation. apt -y --no-download rather thanwholesaledpkg-i permitsnormal dependencyconfiguration, no networkfallback. Entirepostinstallpackage-set mustexactmatch146name/version post-install anchor including92basepackages+54Inst fromlocalapt2.4.14metadata/base-statussolve.119downloadledger is superset, NOT wholesale install. Suppliedbaseidentity is boundtodigest, notpackagebytehash. Realnobleaptmaychoosedifferently; failrequire newanchors. No solverproof or no-downgradeproof yet.

Ubuntuvenv initiallyusesUbuntuensurepip's pinnedpython3-pip-whl/setuptools-whl, then26.2.1/84.0.0hashedofflinebootstrap replacesitandmetadataassertionchecks. WheelsdownloadedbyfixedpublicURL+size/SHA beforepip --no-index --require-hashes fullresolver. CompleteappinstallcannotoccuruntilownCP312sgmlwheelhash+bytesroute reviewed. Currentfetch_verify deliberatelydoesnotfetchlocaloutput.

## Launcher and limits

Csource reviewedcandidate only. Localhostgcc syntaxcheckpassed, NOTtargetcompile/execution. LauncherfixedcandidatePython path, closesnonstdiofds, no_new_privs andseccompdenies socket/connect/bind/listen/send/recv/io_uring, rejectswrongarch+x32. Itisnot generalfilesystem/processsandbox, processdeadline/reap acceptance or512MBproof. It doesnotstartapp/server/client/provider. FinalUSER65534, no appentrypoint. RUN stages use workflowbuildnetworkdefaultforpinnedfetch; no runtime--networkinstruction. PipofflineflagsdonotproveOSnetworkisolationduringbuild. Actualseccompenforcementdependsontargetkernelandmustbetestedlater. No claims beyondsourceinspection.

Dockerpull/build/workflowdispatch separateownerpermission+capableexecutorhandoff. Neitherbuilder norreviewer hasDocker/CPython3.12. No runattempted. ONE139430byteca-certificates-bootstrap.deb is a namedauthorizedbinaryrepoexception forTLSbootstraponly; nowincludedinchange/inputmanifestsandreceipt. Noother.deb/wheel/imagebytescommitted; publicledgers,suppliedhash-pinnedkeyringandcode/docs. Baseimagebyteswerenotpulled. RootconflictsGunicorn22vs23,bcrypt5,extras,nativeprivateinternals,historicalwheelremainopen.

## Revised source gates and remaining limits

Dockerfile has not run; originalblockers1(TLSbootstrap)and2(postinstalledset)wereexpectedtofailoriginaldraft. RevisedcandidateusesbootstrapONECA.debreadonlyextraction,121sortedMozillaPEMconcatenationhash9481fcd95f41b221f02f14d896535fe500bec539bc563c4cdca1acee483a8bdd, explicitCaInfo. PeerverificationNEVERdisabled. Suppliedderivedartifact NOTsystembundleorblacklist-equivalent. AfteraptinstallsCApackage normally, postinstexecutesupdate-ca-certificates/writes/etc/ssl/certs, thenCaInfoSWITCHEStothesystembundleandapt-getupdateverifiesTLS. Bootstrap extractiondoesnotexecutepostinst; laternormalinstallDOES. Stoponbadbundle/hash/TLS.

Postledgerbase92names/versionsboundtobaselayerdigestonly.89snapshot.debhashesaresame-version.deb hashes,NOTlayerpackagefilesproof. libaudit-common/libaudit1=1:3.1.2-2.1build1.1 andlibssl3t64=3.0.13-0ubuntu3.15 haveNOindividual.debhash, versionidentityonly. Openssl3.0.13-0ubuntu3.16plannedwhilelibssl3t64 staysbase. Localaptaccepts version skew; noterrororABIproof. Realaptupgradinglibssl/audit changes146ledger->failnewanchorrequired. No guessedhashes.

Finalimagecontainsgcc/libc6-dev/bubblewraptoolchainbytes, candidateonly. No stripping/multistageclaim. Shelltestsseparatewith explicit ||exit, plan/before/afterloggedBEFOREgateandEXITtrapprintsavailablefailureevidence. Compilesource andshellsyntaxonlylocal, nottargetapt/Docker. InputsremainincompleteuntilownCP312sgmlanchor. Noexisting27a/rootedits.
