# News panel controls

The news-only dark/light switch is session-local and does not change Finder's
independent theme. Manual refresh replaces news panels only, never player
iframes. No automatic news-refresh interval is enabled.

The critical-story panel uses supplied Geo risk_level=CRITICAL and zoned
collection timestamps in a rolling inclusive 24-hour window. Missing, naive,
future and out-of-window times are not presented as recent. It does not apply
Geo risk labels or keyword rules to other-source news. Other policy remains
unavailable. Counts are loaded-read-view counts, not full database totals.
The panel is capped at100 stories with truncation disclosed. It does not send
alerts. Reader/auth failures fail closed, not as an empty successful panel.

This increment does not yet add live video, channel management, source-health
refresh or tab removal. Those remain separate reviewed increments. All live
polling, collection, database writes, mail and deployment remain off.

Counts are rows, not distinct-story identities. The live-reader adapter loads
up to100 rows/project; the panel therefore cannot prove a whole-database24h
count. Sorting assumes API-normalized UTC timestamps. The helper is used
through views() in the API, not as a raw provider-row adapter.

This panel has no fetcher, but configured runtime.py can perform approved
database reads when explicitly enabled. Do not describe the whole project as
incapable of fetching. Full-suite counts are local author test results; focused
review-bundle tests do not reproduce that entire suite.
