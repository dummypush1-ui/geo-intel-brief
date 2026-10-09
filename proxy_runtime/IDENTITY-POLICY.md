# Anonymous proxy boundary

The Finder remains public and anonymous. APP_SECRET is embedded public client material, a compatibility hint only, not private authentication. Knowing it grants no extra routes. No sign-in barrier is added.

Both AI and ships now use the socket peer by default. CF-Connecting-IP and X-Forwarded-For cannot choose identity without an explicit verified trust configuration. Behind a proxy this conservatively shares the peer bucket until its topology is confirmed.

Optional PROXY_TRUSTED_PEERS is a bounded comma-separated list of exact IPs, not CIDRs or wildcard trust. Nonempty trust requires PROXY_XFF_TOPOLOGY_VERIFIED=single_appended_hop. Only those direct peers may supply one XFF header. The last appended address is selected; malformed, duplicate or oversized chains fall back to the socket peer. These assertions are not proof of actual infrastructure. No deployment configuration was changed.

Per-peer limit is reduced to 20 requests per 10 minutes to prevent one verified client draining all 60 shared slots. A shared process-wide limit of 60 accepted AI requests per 10 minutes now limits bypass by many clients. Provider failover also counts every upstream attempt against a separate 60-attempt process-wide budget. Keys do not multiply that budget. Denials may consume a peer slot conservatively. Restart resets process memory; multiple workers/instances have separate budgets. Provider 4xx failures consume upstream attempts too. Distinct-peer flooding can still exhaust the shared budget; protecting the hard cap favors denial over availability. This is not a durable global quota, token/output budget or proof of zero billing. Before enabling network provider wiring, verify free-tier zero-spend account settings and a deployment-wide budget appropriate to the actual instance count.

No provider call, key rotation, live config change or private authentication provisioning was performed. Tests use fixture keys and fake network responses.

Until actual Render proxy peer IPs and single-appended-hop evidence support trusted configuration, ALL users behind one proxy share the same 20-per-10min peer bucket per instance (shared cap60). This is an intentional conservative availability regression from spoofable per-user XFF buckets. No peer IPs are guessed.

PROXY_PER_PEER_LIMIT and PROXY_SHARED_LIMIT are configurable positive decimal integers up to1000, defaults20/60; per-peer cannot exceed shared. Malformed config fails startup closed. Upstream-attempt budget remains60. Raising request limits does not raise this attempt cap or authorize account spending. After trusted topology is verified, individual client20/10min buckets apply, still under shared60 requests and60 attempts. Request/attempt caps bound traffic, not token cost, provider billing or a durable global spend budget.

179: /ships uses a separate 20-per-peer and 60-shared read budget per 10 minutes.
The socket/verified-proxy identity policy is unchanged. AI request budgets
(20 per peer, 60 shared) and 60 upstream attempts remain separate and unchanged.
Snapshots are cached for 30 seconds, with at most 64 known port keys. Unknown
ports return 400. Ships 429 includes Retry-After: 600. Finder stops automatic
polling and blocks manual retry until at least 10 minutes have passed.
Reading the cache causes no AI upstream attempt. Cached status and updated time
are from the snapshot, not a new AIS observation. This is not a shared
cross-process quota or cache.
