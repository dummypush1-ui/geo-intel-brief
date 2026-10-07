# Collector108: partial INACTIVE preparation, not a deployed collector

Separate scratch/review contracts. No liveentrypoint imports this directory;
no trigger installer/worker/fetch/parser/actualDBclient/mail/backup/index included.
Original runtime, Code.gs and public107 remain unchanged. FixtureLedger is only
in-memory specification. DurableLedger is injectedMongoCAS shape; majority/
journal concerns, actualstore/role/mapping not verified or wired. No automatic
expiry takeovers. Unknownwrites latchprofile. Historymax64 stopsnewjobs.

Authenticatedsubmission/status factory tests use CASCollection in memory.
Health reportscollectionfalse. AcceptedHTTP202 DOESNOTstartorfinishcollection.
AppsScript file is ADDITIVE, NOTinstalled, preservesoldbasefunctions/triggers;
headersecret fromScriptProperties, separatecollectionbase, noncepersisted.
Pendingnonce nevercleared beforefutureterminalstatus/recoveryimplementation.

Localtests: Python unittest test_job_contract test_durable; node test_apps_script.js.
No deploymentinstruction/activation included. Save is backupofinertprep ONLY.
Read FREE-TOPOLOGY.md/RECOVERY-GATES.md for outstandinggates. Fullsources/network/
checkpoint/drive/transactionorreconciliation stages areunfinished.
