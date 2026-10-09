# Whole Geo store cursor paging (source-only, default OFF)

PUBLIC_NEWS_FULL_PAGES_ENABLED=false is the default. true requires all existing
public live read/disclosure/mapping/read-only credential gates. No new client or
write privileges. Existing /api/news and loaded CSV remain first100 contracts.
The UI is unchanged in this reader unit. Infinite-scroll UI is a separate unit.

GET /api/news-page accepts single project=geo, q (200), category/country (100),
sort=newest/title/country/score, limit1-100(default25), cursor. Invalid inputs400,
disabled/unavailable503, expired/query-bound mismatch409, busy/capacity429.
Every page still passes existing authorization and public sanitizer/projection.
Opaque random tokens reveal no raw IDs. They are continuation data, not auth.
Tokens bind exact query/limit; one immediately repeated continuation returns its
cached reply, avoiding consumption after a lost response. Older tokens expire.

An injected reviewed Mongo store .find scans the entire collection, no total
limit100 or RAM materialization. At most1000 raw rows scanned per page and100
returned. Filter-after-normalization preserves existing casefold semantics.
A sparse filter can return empty items with next_cursor; this is NOT EOF. Counts
are unknown, never asserted21k. Closed projection; sanitizer rejects oversized
and nested scalar fields. Batch100, server max_time_ms2000, existing socket and
pool bounds. No client query operators, offset/skip, aggregate or DB writes.

Sort is RAW SOURCE Mongo order: created_at DESC, title ASC, country ASC or score
DESC, plus unique _id same direction. This differs from loaded view's normalized
casefold/tie order and is labeled in the API. Missing/mixed source sort values
remain in the single cursor, avoiding unsafe type-bracketed keyset exclusions.
It is a mutable read, NOT a stable snapshot: concurrent edits/deletes/inserts can
change visibility or repeat rows. No whole-store consistency guarantee, current
count or performance claim. Refresh opens a new read. Mongo cursor lifetime,
server query budget and source failures can force restart earlier than expiry.

Worker-local state: max16 active/cached streams; nonblocking global lock permits
one page read at a time.120s idle/30min absolute expiry; background15s sweep plus
sweep on request. EOF/failure/expiry/explicit close closes cursor; worker restart
loses tokens409. Multi-worker routing needs sticky routing or a reviewed shared
continuation service before live enablement. Slow cursor.close can delay sweep;
server/socket bounds are not a hard overall wall-time guarantee. Abandoned UI
streams are reclaimed by expiry, not browser unload promises. No snapshot session.
No index is created. All raw sorts need real source/index/explain evidence before
live enablement or claiming efficient full-store browsing. _id unique tie-break
is a source Mongo property, not verified by fixture tests.

Grounding:
https://www.mongodb.com/docs/manual/reference/bson-type-comparison-order/
https://www.mongodb.com/docs/manual/reference/method/cursor.sort/
https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/query/cursors/
https://pymongo.readthedocs.io/en/stable/api/pymongo/cursor.html
https://www.mongodb.com/docs/v8.3/reference/read-concern-snapshot/
