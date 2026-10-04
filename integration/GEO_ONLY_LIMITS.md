# Geo-only stored news composition

Geo news is the sole stored news view. geo_intel/articles is the user-identified mapping, Any nondefault GEO_DATABASE/GEO_ARTICLES_COLLECTION pair requires a separate GEO_MAPPING_OVERRIDE_VERIFIED gate after source ownership/schema review. newsbot/admin/local/events database names and events/oplog/admin/local collection names are denied case-insensitively even with that gate. No BRICS target or migration. Existing old newsbot store and original engines stay preserved but are not loaded by this separate composition. Events, admin and local are excluded. Live streams remain browser configuration independent of stored news.

New compose_geo_only is an unwired alternative, not a change to private_router/old compose. No default MongoClient; explicit injected factory only. Private login config + NEWS_READ_ENABLED + NEWS_STORE_MAPPING_VERIFIED + explicit URI required before client creation. Factory connect=False, bounded reads100, no indexes/update/insert/write. Finder index/local exact-HSN reader retained when access configured. Failure closes supplied client and redacts connection errors.

Default read-off creates no client and news view remains empty. Screenshot mapping/schema is evidence, not verification of live credentials, permissions, rate-limit suitability or old/new cutover. URI should be configured through secret environment by the owner, never in browser/source. No deployment or live database action performed.

Request-time find/sort/cursor failures close the sole client once and latch reads unavailable. Later requests remain503 until the composition is rebuilt after operator review; no automatic retry or second client. Guarded read uses a lock for request concurrency. Raw errors never returned to UI.
