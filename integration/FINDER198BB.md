# 198b-b same-document receipts and bounded transport, unselected

Default OFF. No production mount, client/env loading, account state, schema
migration, catalog entry enabling or live proxy request. AI catalog remains
EMPTY/DISABLED, NVIDIA excluded; ships require closed42codes+ALL. Tests use
local disposable CAS and mocked sockets/transports; no upstream network.

Reviewed v2 contract: SAME geo_intel.finder_budget198/shared-finder-v1 document,
schema2 with original counter/ticket fields +receipts64. Explicit owner-operated
preprovision/migration required, no automatic migration; v1 adapter unchanged.
RevisionCAS combines nonce/body/identity hashes receipt +budgetcounter+active
reservation atomically; second CAS transitions reserved->send_started BEFORE
network. Original60proxycalls/600s/global1inflight/norefund rules preserved.
Full64receipts failclosed; noTTL/drop/reset/archive. Nonce duplicate withdifferent
body/identity refuses. Same nonce returns status only, nevertransport/cacheanswer.
No prompt/response text, secret/sessiontoken stored. Receipt identity hash includes
required principal_hash plusoperation/provider/model/port. A future HTTP adapter
must derive this hash from authenticated UID on eachrequest, nevertrust caller's
principal_hash. This factory does NOT prove principal authentication itself.
Receipt hashes are private metadata, not a public status route. No mount here.

Receipts keepnoncehash/bodyhash/identityhash/fence/phase/start/deadline and only
complete response status/hash/length. State validatesclosedtypes/hashes/active
matching. UnknownCAS never retried; completed response is returned only if
receiptCAS succeeds in time. Lost CAS ack may leave complete receipt; a later
same-nonce call returns statusonly, never resends. Unknown/late/failure stays
send_started orunknown_held/globalhold pending explicit ownerreconciliation.
No takeover/expiryrelease. Manual reconciliation and futurearchive contracts
must exist beforemount; no clearing mechanism here.

Actual transport: exact fixed hsn-ai-proxy.onrender.com HTTPS443/routes, allDNS
answers checked public/nonmixed beforefirstsocket; pinnedpeer+hostnameverified
TLS, no redirects, oneconnection/no retries/fallbacks.20s parent supervised
whole deadline includes DNS/TLS/read;256MiB childAS/32FD/emptyenv/secret in stdin,
not argv/logs/errors. Fixed Host/Content-Type/x-app-token/Content-Length/Connection
headers only; no callerheaderforwarding. Request16KiB; response1MiB beforebody
reads, strictJSON content-type/identityencoding/unambiguous framing/no duplicate
headers; finite headercount/valuecaps. Late/partial/redirect/invalid/secret-echo
(includingJSONescapes)/childstderr/status/protocol anomalies held. Childkilled/
reaped on timeout. Installed childSHA checked beforelaunch. A model/path plan
is reconstructed from disabledcatalog/closedport set beforetransport.

Transport request20s <ticket25s allows receipt overhead, not a guarantee Mongo
will finish. Ledger operations timeout/concern failures remainheld. Brokerabort
DOESNOTproveproxy/providerstopped. UnitPROXYCALLS, upstreamattempt countunknown
(keyrotation). Independentbrokercaps doNOTrepairproxyCORS/XFF/quota/redirect/
rotation/server-secret exposure. Separateproxyhardening+ack remainsneeded for
end-to-endbudget. No currentdeployedSHA/key/model/freeentitlementfacts verified.

Source composition not an HTTPbroker: no loginUI/publicpasschange/198a mount.
Authenticated session+Origin+CSRF+singleworker/ownerDBgrant+liveproxyfacts are
latermountprerequisites. AI provider-specific request schema still laterwork;
AI disabledtoday so no payloadcanselecta model. No providerusage/paidcall tests.
Two clients with differentauthenticatedprincipal hashes cannotreuseonenonce.
No savedanswer/result delivery onduplicate; usermustretainoriginalresponse.
