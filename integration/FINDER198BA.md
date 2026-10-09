# 198b-a source-only durable proxy-call budget and closed connector contract

Not a live broker. No transport implementation, client, environment selection,
production mount, schedule, model activation or provisioning. 198a still503.
Model catalog EMPTY/DISABLED; Groq/Gemini/Mistral only, NVIDIA excluded. Enabling
entries later requires owner scope, live vendor availability/free entitlement,
current deployed proxySHA, configured provider keys and live health JSON.
Client model comments and wildcard upstream acceptance are not verification.

Reviewed source decisions: fixed geo_intel.finder_budget198, single preprovisioned
_id=shared-finder-v1, majority+journal/wtimeout<=5000 +majority read, revisionCAS,
60 PROXY CALLS per600seconds, global1inflight, consumed BEFORE transport, no
refunds, no takeover/expiry release, unknown/expired held for separate explicit
reconciliation. Dedicated credential must not alias reader/account credential;
actual later client factory must validate that, this injected adapter creates
none. No upsert/create/index/TTL/purge/reset/reconciliation implementation.
Read-only inspect_budget checks exact single identity find/listIndexes/update
role only, fixed mapping/_idindex/noTTL/preprovisionedclosedstate. Constructor
review fields gate source but never prove owner permission or live role.

State: _id, revision, window_start, calls, fence, active, last_clock. Active
key/fence/started_at/deadline<=25s/phase inflight|unknown_held.4boundedCAS contention
iterations; unknownreceiptfailclosed/no network. Completion within ticketdeadline
clears active, NEVER refunds; incomplete/late remainsheld. Clockrollbackrefused.
All requests need distinct nonces; adapter is NOT durable request-id dedup after
settlement and NOT an HTTP retry mechanism. A future broker must not replay a
consumed request under a new or old nonce; no automatic retries/fallbacks here.
No claim of audit-history retention or saved result beyond currentticket/counters.
A separate reviewed receipt/idempotency layer is needed before mounting transport.

Connector CONTRACT fixes https://hsn-ai-proxy.onrender.com and exactpaths; no
arbitraryURL, callerheaderforwarding/redirect/fallback. Ships acceptsALL+42source
portcodes only. AIcatalogdisabled, no live model selectable. Requestcap16KiB,
responsecap1MiB,20secondtransportdeadline, exactlyONEproxyrequest/noautoreties.
These are plan metadata, NOT an implemented bounded network connector. Actual
future transport must enforce while reading bytes, DNS/TLS/fixedhost/noredirect,
and session+Origin+CSRF via198a before durable reservation and before network.
BackendFINDER_PROXY_BASE_URLmustexactfixedorigin;FINDER_PROXY_SECRET48..256visible
ASCII, no secret returned by config validation. No live token loaded or tested.

PROXY CALLS is the accounting unit, NEVER provider attempts. Current proxy may
rotate an unknown keypool on401/403/429/errors. A broker timeout/abort does NOT
prove the proxy/upstream stopped; unknown remains globalinflightheld with no
automaticrelease/retry. End-to-end attempt bounds and acknowledgement are a
separate proxy-hardening work item, not solved by these independent brokercaps.
Source-only success in fixtures is not deployed runtime or free entitlement.

## Current source grounding, October9

Read original proxyrepo push2006/finder-hsn-codee HEAD
9133270856bb77170956b707bafe260997690d80 via live repository source. render.yaml
nameshsn-ai-proxy/nodeproxy.js/free/node22, but actual deployedSHA unverified.
Public /health fetch503 is inconclusive(possiblecoldstart), NOT downproof.
Source has4providersinclNVIDIA/wildcardGemini/no modelallowlist; HITSMap60IP/10min,
trustsCFIP/FIRSTXFF, clearsALL>5000keys, no durable/shared budget/inflight. CORS*,
publicclientAPP_SECRET.2e6charbody,150sabortperkey, unboundedresponse/default
redirect/rotation. Do NOT inherit these policies. Repo hardening is later
separate work; no otherrepochanges/settings/providercalls in this unit.

Sources read:
https://github.com/push2006/finder-hsn-codee
https://hsn-ai-proxy.onrender.com/health

Validation only local disposableCAS/read-onlyfakeclient and closedplans.
No UI or visual change. No Atlas state/role/key/server/upstream accessed.
