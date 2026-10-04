# Trade-country page and watchlist

Independently written. Reads supplied normalized Geo and BRICS rows under existing private preview authorization. No new clients, collectors, timers, writes, delivery, deployment or cutover.

Exact original country/region labels only. No headline inference or country-code aliases. Counts are loaded rows, not unique articles, full database coverage, trade flow, risk or verified tariff changes. Country views cap display at 100 and preserve collection labels. Finder matches use only the existing verified-index endpoint, on manual click, with no new guessed HSN codes.

Watchlist holds at most 20 labels in this browser's localStorage. It does not sync across devices or activate alerts. Storage failures are visible. Empty results and unavailable reads are distinct. Future/missing timestamps are displayed as supplied, not interpreted as verified event dates.

New URL: /workspace/countries. No public exposure: default authorization denies it. This is a local offline increment pending independent review and private backup, not a deployed app.

Whitespace-padded stored labels are not offered in the selector. They cannot be matched through the trimmed UI and remain uncounted there. Counts per project cover all matched supplied rows and may exceed the 100-row display cap. The supplied normalization layer converts missing/non-string country values to strings before this page reads them; direct unnormalized dicts are not accepted input.
