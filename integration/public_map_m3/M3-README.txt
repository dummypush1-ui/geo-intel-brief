# M3 manual hosted streets candidate

Default OFF. This is preparation, not deployment or proof of public availability.

`PUBLIC_MAP_M3_ENABLED=true` requires exact `true` values for
`PREVIEW_PUBLIC_SAMPLE_ENABLED`, `PUBLIC_MAP_ENABLED`, and `PUBLIC_MAP_M2_ENABLED`.
The old raster-provider flag remains prohibited by M2. Existing sample/live
builders mount this module only with the new flag. Nothing changes when it is OFF.

## What changes on the map page

- M2 Natural Earth countries, bounded historical WPI 2019 ports, country-tagged
  latest-100 news and both NGA notices remain. Load the reference map first.
- "Show online streets" creates a MapLibre layer only on a deliberate click.
  No remote styles, tiles, fonts or sprites are requested on page/reference load.
- Bundled MapLibre GL JS 5.6.1 CSP renderer/worker and the 0.1.3 Leaflet adapter
  are pinned, with original license notices and npm integrity provenance.
- Unmodified Liberty style captured Oct15,2026 is local and pinned. Its imagery,
  TileJSON, vector tiles, sprites and fonts are fetched directly by the browser
  only from `https://tiles.openfreemap.org`. No official OSM tile host is used.
- Request transform and page/worker CSP reject other providers. Credentials are
  omitted; page referrers are suppressed. News/search bodies and DB credentials
  are not sent. Remote servers still see requested map areas and connection/IP
  metadata; the provider's privacy policy also covers Cloudflare processing.
- Static OpenFreeMap / OpenMapTiles / OpenStreetMap credit is always visible in
  the map corner without opening a control, with source and license links.
  Software/style notices are linked below the optional-streets control.
- At the first renderer/source error or 15s startup timeout, the street layer is
  removed. Natural Earth remains, the zoom cap returns to8, and no retry starts
  without another click. Stop, hidden-tab and pagehide also remove the layer.
- One renderer worker, 4 parallel image requests and maxTileCacheSize64 are
  configured. These are renderer settings, NOT a global vector-request rate or
  memory cap. The M2 simulated raster gate does not govern MapLibre vectors.
- Online max zoom18 corresponds to MapLibre zoom17 through the Leaflet adapter.
  Country-tagged news is never represented as a precise street event. Historical
  ports are not live positions. This is not navigation or legal-boundary advice.

## Provider review, Oct15,2026

https://openfreemap.org/ says public use is free, without request/map-view limits,
registration or keys. It offers no SLA. https://openfreemap.org/tos/ (updated
Oct14) requires an integrator18+ who can enter the agreement and has organizational
authority if applicable. This eligibility has NOT been independently established.
The service may stop without notice. No automated collection is implemented.
The offline allowance (3000tiles or50MB/download,4parallel, identifying User-Agent)
is not an offline capability of this candidate.

https://openfreemap.org/privacy/ (updatedOct8) covers embedded public tiles:
browser/referrer/time/OS logs without IP normally, IP/URL in errors for7days,
security IP logging up to30days, and Cloudflare processing. `no-referrer` limits
what this app sends but cannot remove connection metadata or change the policy.

Sources and notices:
- https://openfreemap.org/quick_start/
- https://github.com/hyperknot/openfreemap-styles/blob/main/LICENSE.md
- https://github.com/maputnik/osm-liberty/blob/gh-pages/LICENSE.md
- https://github.com/maplibre/maplibre-gl-leaflet
- https://registry.npmjs.org/maplibre-gl/5.6.1
- https://registry.npmjs.org/@maplibre/maplibre-gl-leaflet/0.1.3
- https://tiles.openfreemap.org/styles/liberty
- https://tiles.openfreemap.org/planet

## Validation and remaining gates

`tests/test_public_map_m3.py`: flags, pins, source URLs, both builder compositions,
GET/HEAD/host/query/method guards, no startup server network and OFF parity against
the frozen immediately preceding M3 baseline builders. A Node harness tests the
exact source allowlist function independently of browser CSP. Installation requires
the exact mounted M2 shell, not merely a matching route name.

`tests/browser_public_map_m3.py`: actual bundled WebGL renderer/worker with pinned
Liberty style. Every remote request is intercepted locally using synthetic empty
vector tiles/raster/sprite fixtures. Tests manual load, responsive widths320/390/
1100, in-map attribution, high zoom and reset, stop, startup failure,503 fallback,
malicious TileJSON destination rejection, synthetic-click rejection, actual15s
hung-source timeout, reference refresh after failure, hidden
removal and no auto-restart. These fixtures prove plumbing/fallback, NOT the
correctness or current availability of live street labels/geometry/fonts.

Before activation: confirm eligible integrator/terms and privacy authority, review
this candidate independently, obtain each push approval, then conduct a bounded
real-provider smoke test and review actual deployed CSP/headers/browser pixels.
No token, push, Render change, service monitoring or cutover is part of this batch.
