Copyright (c) 2026 Push (wrapper/selection). Wikidata coordinates are CC0; no other third-party text is copied.

# Reference data status (retrieved 2026-10-04 20:36 UTC, 2026-10-05 02:06 IST)

## chokepoints_wikidata.json - REAL data, 12 rows
Source: Wikidata via its API (wbgetentities, props labels/descriptions/claims/info), read once, polite rate. Each row's
coordinate is the single P625 value of the item, normal rank; revision id recorded per row in field wikidata_revision. Each item page returned HTTP 200:
https://www.wikidata.org/wiki/Q79883 (Strait of Hormuz), Q48359 (Malacca), Q83318 (Bab-el-Mandeb), Q899 (Suez Canal), Q7350 (Panama Canal),
Q35958 (Bosporus), Q6514 (Dardanelles), Q36124 (Gibraltar), Q104662 (Oresund), Q159898 (Dover), Q127031 (Taiwan Strait), Q4092 (Cape of Good Hope).
Licence read at https://www.wikidata.org/wiki/Wikidata:Licensing : "All structured data ... is released into the public domain under Creative Commons Zero."
Item identity: chosen from wbsearchentities results by label and description (e.g. Q4092 is the headland, not the colony or paintings).
Limits: points are display centres only. Canals (Suez, Panama) and the Cape headland are single points. Coordinates were sanity-checked
by the builder against general geography, NOT against a second independent source. The EIA page
(https://www.eia.gov/international/analysis/special-topics/world_oil_transit_Chokepoints) returned only site navigation text when fetched, so the
name cross-check against EIA was NOT done. The list of 12 is the builder's own selection; no volume or status claims are made.

## Ports - NOT included
Natural Earth ports page https://www.naturalearthdata.com/downloads/10m-cultural-vectors/ports/ shows version 5.0.0, "derives from High Seas ... in the public domain".
Terms page https://www.naturalearthdata.com/about/terms-of-use/ says all Natural Earth vector data is in the public domain.
But the download links on that page (observed href .../http//www.naturalearthdata.com/download/10m/cultural/ne_10m_ports.zip, also ?version=4.0.0 and 2.0.0)
all returned HTTP 500 on 2026-10-04, so no port rows were created. Not guessing other download URLs.
NGA World Port Index: excluded (licence wording not verified).
