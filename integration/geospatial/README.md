Copyright (c) 2026 Push

# geospatial (offline display modules)

Python (pure, no I/O): `validate_features(items)->(features,report)`, `ship_view(observation, now, stale_after=15min)->dict`,
`map_payload(news_features, ports, chokepoints, ships, now)->dict`, `project(lat,lon)`, `bbox_rects(bbox)`.
JS (ES module): `mountMap(element, payload, options)` and `dispose(element)`; link `geo_map.css` (no inline style needed).
Ship age threshold 15 min is a proposal: AIS position reports normally arrive within seconds to minutes.
Caps: 1000 features, 1000 ships in, 500 ships shown, 200 news; truncation is flagged.
No tile, network, stream or key use. Preview/fixtures are synthetic.
CSP needs for this offline build: script-src 'self' (module), style-src 'self', img-src 'self' data:, connect-src none.

Notes: items may carry `"fixture": true`; the table then appends "(fixture)". News `risk_level` text, when supplied, passes through unchanged;
this package derives no risk, threat or congestion value. Wrong-kind feature rows are counted in `report.wrong_kind_dropped`.
Stale ship markers are dimmed. Markers at longitude +-180 are inside a padded viewBox.

URL rule (Python _safe.safe_https_url and JS safeUrl): printable ASCII only (percent-encode the rest), https scheme, no "@" in the authority,
hostname [a-z0-9.-] with alphanumeric ends and no "..", last label not all digits, port <= 65535. JS also runs new URL() and may reject a few more
(for example malformed xn-- labels), so: JS accepts implies Python accepts. Tested with fixed vectors (exact match) and a seeded fuzz (one-way).
