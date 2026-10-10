# Port-weather card wrapping (231)

On phones, weather values ran off the right edge; scrolling right hid labels
and the starts of the values. The weather card now fits two columns to the
phone and wraps long values. Labels and full values can be read together
without sideways scrolling. Values, sources, dates and requests stay the
same. Other Finder tables stay unchanged.

CSS only: src/style.css global .report-table min-width680px remains. New
#portwx-pick + .report-table-wrap .report-table selector matches only the
successful weather data table next to its original select. min-width0,
width100%, fixed layout, cell wrapping, first-column40% with label words
unbroken. No hidden content, smaller fonts, ellipsis or max-height. Wrapper
keeps its original overflow:auto fallback. src/app.js SHA bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313 unchanged.

New browser_weather231 and test_weather231 check table/cell bounds, labels,
source/date, native port control focus/Tab/ArrowDown/Enter/Escape, model503
states and original formatters with long numeric fixture values/degrees0/359.
Expected directions both round to N via the original formatter. No formatter
or text changes. All fixture numbers SIMULATED, not official weather. Caption
is outside raw card captures (result.json); no fixture label covers the card.

BEFORE230 final390 screenshots copied verbatim with their original UTC result
and hashes. Fresh230-tree probe at320/390/1100 light/dark failed geometry at
320/390, exit1. Initial harness syntax error corrected before that recorded
geometry run; no product error claim from that attempt. AFTER from two final
consecutive runs only; semantic equality excluding times. Actual final30card
pixels inspected via five contact sheets: success, stress0,stress359,marine503,
forecast503 at320/390/1100 both themes. Full values/date/warning fit; long
wave period wraps; label words intact. Not real weather/model accuracy or
all browsers/devices. Chromium154.0.8037.57/Python3.10.12/Playwright1.63.0,
Nodev22.23.3. Frozen1791576000000/random0.25/AsiaKolkata, no sleeps.

Test-only scope mutations occur after all captures: widen selector to global
.report-table and detect non-weather minWidth changed; insert a sibling after
the weather select and detect selector no longer matches/minWidth680px.
Restore both. Port statistics retains680px and horizontal scroll at320.
No CSS/DOM mutation is used to make the final card pass. Native table markup
unchanged; accessibility checks cover the control, not a full accessibility
audit. Five probe modes use exact GETforecast/marine mocks; expected FX read
aborted. Original230 six-case regression has unchanged endpoint/counts and
CSP; its geometry now checks fitting cells instead of historical clipping,
with dated231 supersession comment. FINDER-NETWORK230.md untouched, historical
clipping finding superseded by this document.

Local double rebuild commands in audit. index.html now8e1ce9c7fa5da880085afb2b8a20e6fbc3195d8b24f4ffdde4bee09c787d0967;
offline.html now0e2e85ea54f276c3c50984e8c26b9400e1deee9f4b8a035a8866e56c2455b65b.
Public offline cache ID4f48ae1b3cd7 -> c100d1017b7c is a separate derived change,
only relevant when future snapshot explicitly served/used. No live activation.
Dataset data.d6d1b417562b.js and sw.js unchanged. Source.css, snapshot hashes,
adapter hash pins, build receipt and preservation note updated; adapter logic
unchanged. 229/230 index pins updated with231 comments. 230 historicaldoc
not rewritten. Default new wrapper explicit SKIP unless RUN_WEATHER231_BROWSER=1;
missing Chromium/Playwright explicit SKIP, never browser PASS.

230/229/228/nested/static/offline/198d/ships226 regressions PASS on finalsource.
One combined120second regression call timed out after all8logscompleted; logs
read for completion before continuing, no side effect retried. No DB access,
sends, mount, serving, deployment, activation or wiring. Full project remains
incomplete. Scope is local code/snapshot review, not live operation.
