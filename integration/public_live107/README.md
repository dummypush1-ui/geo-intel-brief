# Reviewed public Geo article reads107

Additive public_live107:app entrypoint. Default PUBLIC_NEWS_READ_ENABLED=false
delegates unchanged public106/sample/private rollback. Exact true requires ALL:
PREVIEW_PUBLIC_SAMPLE_ENABLED=true, PREVIEW_GEO_ONLY_ENABLED=true,
PREVIEW_ACCESS_ENABLED=false, NEWS_READ_ENABLED=false,
NEWS_EVENTS_READ_ENABLED=false, FINDER_NETWORK_PREVIEW_ENABLED=false,
NEWS_STORE_MAPPING_VERIFIED=true, PUBLIC_NEWS_DISCLOSURE_VERIFIED=true,
GEO_READONLY_CREDENTIAL_VERIFIED=true. GEO_DATABASE=geo_intel and
GEO_ARTICLES_COLLECTION=articles only; URI required in GEO_MONGODB_URI.

These assertions do not themselves prove owner permission, mapping or Atlas role.
Operator must check source and read-only credential independently before enabling.
No URI or credential copied into evidence. Read-only role cannot be introspected
or proven by facade; a privileged URI remains privileged and must not be used.

Canonical HTTPS origin validated before client creation. Existing read facade with new timezone-aware TLS factory,
timeouts5s/pool4, find-only wrapper. Reader exact geo_intel.articles, limit100,
created_at descending, maxTimeMS2000, cursor always closed, whitelist projection.
Mongo dates read with tz_aware=True (UTC), avoiding naive datetime loss.
Additive sanitizer accepts exact bounded strings ONLY for URL/title/display fields,
nullable/time fields accept bounded strings or timezone-aware datetime; score is
finite exact numeric, not bool. Nested dict/list/objects omitted without str().
Malformed requiredURL/title rows dropped; all private raw keys discarded before
cache/normalization. Historical private normalizer unchanged.
Existing public normalization strips IDs/emailed/receipt/private keys and unsafe
URLs. All allowed output fields are public disclosure, including summary/source,
country/category/timestamps/risk/credibility/score. Original source content not
independently fact-checked; page is a bounded stored-news read view, not truth proof.
No arbitrary collection or client from request. Client factory injectable only
for reviewed tests; source env controls production, no network before gates.

Per-process60-second read cache, one fetch at a time, lock acquire2s bound.
Successful empty collection is legitimately empty. Read error clears cache,
closes client, latches unavailable until process restart after operator repair;
API503 sanitized, never replaces failed read with empty success. Latest100
stored documents selected before normalization, so invalid rows may reduce count.
Cache means manual refresh need not immediately reflect DB change. No polling.

Public GET/HEAD allowlist unchanged; write/private/events/full export/PDF/digest
routes denied. Offline Finder unchanged; no private saved keys/localStorage.
Public news label and loaded100 scope replace empty-sample label. Sample/private
fallback unchanged. No old source,105/106evidence or frozen baseline changed.

User-operated Render Start Command after reviewed save:
gunicorn public_live107:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 30

Additional live-public env values after owner/operator verification:
PUBLIC_NEWS_READ_ENABLED=true
NEWS_STORE_MAPPING_VERIFIED=true
PUBLIC_NEWS_DISCLOSURE_VERIFIED=true
GEO_READONLY_CREDENTIAL_VERIFIED=true
GEO_DATABASE=geo_intel
GEO_ARTICLES_COLLECTION=articles
GEO_MONGODB_URI=(user enters read-only URI directly in Render, never chat)

Keep106public flags/origin/Python unchanged, particularly NEWS_READ_ENABLED=false,
NEWS_EVENTS_READ_ENABLED=false and FINDER_NETWORK_PREVIEW_ENABLED=false.
Rollback PUBLIC_NEWS_READ_ENABLED=false returns sample106 with no Mongo client;
private fallback still uses original reviewed private settings. No collectors,
mail, migration/index/write/otherDB requests, no Render changes by task.

Public workspaceJS exact-code button disabled via scoped response transform;
private sourceJS unchanged. Text bounds2048 URL/title,8000summary,200otherfields,
100dates, UTF8<=4xcharacter cap; lone surrogate invalid.12focused tests pass.
V2initial test found uncached return used raw rows, now corrected to sanitized
cache on FIRST fetch and all subsequent requests; adversarial firstfetch PASS.

Final13focusedPASS including cold+expiredcache across9publicJSON/CSV endpoints
with hostile nested marker/ID absence checks. Full1166unique/runPASS with existing
1expected limiter failure and1optional pikepdfskip. Fixture390/1280browser
PASS nooverflow/errors/externalrequests, publiccodebutton absent; pixels
inspected, readable news card/loadedlimits. No liveDB or credential inspected.
