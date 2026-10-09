# 226: Finder supplied ship response presentation

Real source parity work in the unselected 198d account panel: all 42 static port
choices and a bounded vessel table, with the existing bounded raw JSON retained.
This adds no mount, asset serving or activation. Own-key original files untouched.
Pins: preserved merged src/app.js f8ecf57f73c28c376c4508f2ce7315f3ffad0a8a26d925a9782db6bb53e38f91;
proxy.js dc6a77bd88d294a84c012d9e6928fb24ed5e8b3504877f7dcf13950829e0869c.
Live upstream Finder was also read, but is a DIFFERENT checkout; those upstream
hashes are not the test pins. Audit includes credential-free indexed excerpts.

Options come from indexed proxy AIS_PORTS and AIS_PORTS_WORLD, never response
names. Tests require exact 42-code and name equality and connector PORTS equality.
Supplied response requires every static port exactly once with matching name and
bounded integer count. Port counts are whole-fleet per-port values regardless
of filter, not selected count. They are neither summed nor displayed as fleet.
Headline count is matching vessels before the upstream 150-row slice: show
"Showing X supplied rows; source reported Y", not a current coverage claim.

Strict closed success shape only: ok True, bool warming/stalled, canonical ISO
milliseconds timestamp ending Z, count 0..6000, exactly 42 ports and <=150 vessels.
MMSI is a 9-ASCII-digit STRING: indexed aisUpsert uses String, not a number.
Text fields may be null or strings <=120; controls, bidi overrides and invisible
ZWSP are refused. Speed finite 0..102.3 knots or null, latitude -90..90 and longitude
-180..180 are finite non-null numbers. Seen seconds exact integer 0..31536000
(one year); bool is not number. Unknown shapes or limits fall back to raw JSON.
Bounds are presentation rules, not proof the upstream enforces them. No rows are
silently dropped. ETA is literal "as reported". Timestamp is displayed literally,
not toLocaleTimeString, no calculated "ago" or local clock/freshness assertion.
Coordinates validated but not shown; no maps or links. Empty says "Supplied
response has no vessels". Warming/stalled are as reported, not freshness proof.

Dynamic text uses textContent only. Hostile HTML remains literal. Coverage text
is the exact original paintShips warning: coastal volunteer AIS, crew-entered
ETA/destination may be stale, not for navigation. Its "Free data" wording is
preserved original copy, not independently verified current entitlement.

Only a completed success-shaped body becomes a table. Errors, holds, replay,
401/403 and sign-out behavior are unchanged. The raw bounded pre remains visible.
The view triggers no request. Port selection alone never requests. A click uses
198d's existing POST account/nonce broker route, which causes upstream GET /ships.
Original proxy GET requires app token and read limits; no new path added here.
Unlike original Finder's 60-second polling, 90-second abort and automatic retry,
198d keeps single-click, 25-second deadline, no polling or retry. No credentials,
provider secrets, model catalog, backend, DB or runtime changes.

Synthetic browser fixtures only: 320/390 widths, 150 long-name rows, internal
horizontal table scrolling, keyboard dropdown, malformed fallback and client
hold states. No real accounts or external requests. All live gates remain open.
