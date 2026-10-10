# Public offline shortlist CSV and keyboard scroll (232)

Public offline shortlist exports now use the same safe CSV quoting as the
online preview. Formula-like cells get a leading apostrophe, NULs are removed
and invalid surrogate characters replaced. Valid Unicode, quotes, commas and
newlines remain. Six columns, order, code/description/duty/source values and
hsn-shortlist.csv filename stay unchanged. The shortlist table gains the
online preview's named, focusable scroll container. This supersedes the
offline CSV/shortlist caveats in FINDER_PARITY_PLAN; the original196 offline
limits document stays historical. No new persistent settings or live features.

finder_offline.shell calls the existing shortlist_scroll and shortlist_csv_safe
from finder_nested after the raw-source SHA gate and manual-ships transform,
before CSP script hash calculation. No copied sanitizer. Missing/doubled/already
applied anchors fail closed. Header and meta script hashes independently
recomputed; no unsafe-inline script permission, connect-src none unchanged.
Range returns full transformed200; no-store,403 gate and public marker unchanged.

BEFORE on clean7333a8a actual local cached offline page: formula/tab/CR/newline/
format-control notes exported unprefixed; NUL survived. Original Blob already
replaced an unpaired surrogate in downloaded bytes, so no before/after byte
change is claimed for that row. Astral/quotes/newlines survive both. Python3.10
CSV refuses NUL: probe uses a parsing-only sentinel then restores NUL in result;
raw downloaded CSV untouched. byte.decode keeps CR instead of universal newline
conversion. Initial harness parsing/desktop scroll wait/expected CSP errors
were corrected before final recorded BEFORE and AFTER, not product changes.

BEFORE outer width already fits320/390/1100 in this fixture. Missing focusable
container, not proven whole-page overflow. AFTER Tab from print reaches named
region at every width;320 ArrowRight scrolls and End exposes Remove.390/1100
fixture already fits, no forced-scroll claim. Actual final images inspected at
320/390/1100 light/dark, plus320 light/dark end-scroll: readable public banner,
code/description/note/duty/Remove; keyboard outline clear, no page overflow.
Full-page images include12rows; viewport crops used for readability inspection.

Two final consecutive browser_offline232 runs PASS, stable semantic results
excluding timestamps and animated scroll fractions normalized to nonzero bool.
The raw keyboardScroll pixel number is not stable (for example1versus2).
Real original CSV click/download from cached-local offline document, not mocked
quoting.12 synthetic in-memory notes only, no real device data. Online normal
export matches normal offline row; other non-note fields equal for all12rows.
Fresh offline reload clears notes/shortlist/key; Storage writes0 offline. Old
cache deletion, unrelated cache retained, explicit install/clear, no private
paths cached. Existing online bootstrap expected Frankfurter blocked-connect
CSP messages only; offline has no requests. No script/style CSP weakening.

Derived cache roll separate from activation:
geo-public-finder-c100d1017b7c-v1 -> geo-public-finder-f08e061a1af2-v1.
f08e061a1af2 is first12hex SHA256 of actual complete served offline response
bytes, f08e061a1af28f591b1e4b5c10377967cfbe4a0fcc6a516e346562be59c7ed10.
Test recomputes served response SHA and compares CACHE, fails if bytes change
without roll. Worker logic byte-identical except constant. Existing activate
step deletes old snapshot cache. Matters only on future explicit serving/use.
Raw offline.html/index.html/app.js/dataset/sw.js/build receipt unchanged.
Local raw provenance double rebuild inputs/outputs equal saved receipt; no raw
rebuild or receipt byte change needed. Pins/audit record this separately.

Source regressions: weather231/network230/own-key229/report228/nested/static/
offline/198d/ships226 PASS. Units offline232/offline/nested/provenance19OK1default
browserSKIP. Browser wrapper RUN_OFFLINE232_BROWSER=1 opt-in; missingChromium/
Playwright explicitSKIP. Chromium154.0.8037.57/Python3.10.12/Playwright1.63.0,
Node22.23.3, frozen1791576000000/random.25/Kolkata. No real provider/weather/
FX/AI/manualAIS/hostedHTTPS/Safari/quota/full spreadsheet-client proof.

No DB, send, mount, serving, deploy, activation or wiring. Full project remains
incomplete. Existing raw Finder source and other tables are untouched.
