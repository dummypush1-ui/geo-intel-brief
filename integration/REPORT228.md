# Finder report popup repair (228)

## Visible changes

The report opens the same way and keeps the same product text/data/AI fallback.
Its Print button and page-number setup run from the Finder opener rather than
scripts inside the popup, so they work with the existing security policy.
Print layout no longer places the fixed footer over report text. Copyright
now appears at the document end in print, not on every page. Screen footer
stays fixed. No security rule or AI/network access is opened.

This is local code and generated snapshot preparation, not serving, mount,
deploy, live SW activation or runtime wiring. No DB/send/cutover changes.
Native OS print dialog, live AI/provider behavior and other browsers remain
unverified. Existing feature-finder and finder-network failing scripts are
not repaired here. Historical REPORT227.md and SHIPS226.md retain their old
source pins and findings with a dated supersession note.

## Mechanics and limits

buildTemplateReport returns no executable script or on*= attribute. It keeps
21 ordered sections (01,01A,02..20), titles, esc() text, product code, Data
edition/error note and copyright. Print button id tpl-print gets a listener
from the opener, calling the captured popup's w.print. A later print throw is
caught without falsely displaying a popup-blocked error. Setup failure still
uses the original report-open error path; no-key gate and finally unchanged.

setupTemplateReportWindow stores a one-shot guard on the popup document.
It waits for complete readyState or one load event, then actual doc.fonts.ready
or a 1500ms deadline (no polling). Actual report uses system fonts; the tested
report's fonts are ready before measurement. If a font is still pending at
the deadline, layout is measured then and is not remeasured later. That is a
bounded fallback, not a promise for custom late web fonts. No font requests
are added. The exact helper is tested in a synthetic realm for late ready,
load, deadline, closed-popup guards, idempotence and later print throws.
Actual Chromium tests exercise the real report and its font/layout effects.

Pagination retains original TPL_PAGE_H=994, section order, min-height and
Page X of Y screen stamps. It uses popup-owned elements. Print uses natural
flow, hides stamps/actions and overrides min-height; print footer is static.
No @page margin boxes, content duplication, removed contents or hidden text.

Popup reload/navigate loses its written document/listeners/pagination. Reload
was observed as about:blank with zero report sections. Reopen from Finder to
regenerate; this is not a durable report URL. Old inline behavior lived in the
old document and cannot be promised after a reload either, but attaching from
opener does not reinject listeners into a replacement document. This lifecycle
change is explicit, not hidden or claimed supported.

## Pins and local snapshot consequences

| Path | Current SHA256 |
| --- | --- |
| src/app.js | bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313 |
| index.html | e2ed3326bfb8ca0805677e026438ff412611eef712526dea17b49d6c7fa30625 |
| offline.html | b55d6b0cf2be2ff3ddf366c4afa23d452367265ef2e85a31b9a4fb6cd411b486 |
| data.d6d1b417562b.js | d6d1b417562bad99e7b434605d63966772749d573375fb10d74ee52cb6bb82f6 |

Dataset filename/bytes unchanged. sw.js unchanged. Local index/offline bytes
changed. Public offline served snapshot bytes changed, so its explicit-opt-in
cache id changes from geo-public-finder-2491a5a38160-v1 to
geo-public-finder-4f48ae1b3cd7-v1. Returning devices would get the revised public
snapshot once the new code is served and their offline flow is used. No live
origin's cache or SW is touched now. Privacy/no saved keys/notes behavior is
unchanged and its existing offline browser probe passes.

Own-key pins in test_finder198d/test_ships226 and served-copy SOURCE_SHA/
OFFLINE_SHA are updated with 228 notes. Build provenance is generated locally
with scripts/finder_provenance.mjs prepare(), which double-builds and confirms
inputs unchanged. Node v22.23.3. Exact portable rebuild command is shipped in
the audit artifacts, writing only index/offline/sw and receipt, refusing any
changed dataset. No refresh.mjs/automate/provider read is run.

## Evidence

BEFORE: verbatim copies of 227 final indexed-run report/PDF/PNG/probe, original
capture times exactly as saved in the copied probe: run started 2026-10-09T23:07:00.683204+00:00 and finished 2026-10-09T23:07:21.943997+00:00. Their source is the 227 tree ffe6092,
report print counter0->0/CSP violation, pagination0 effects, fixed footer
covers Contents 08/17. They are not recaptured or relabelled as new before.

AFTER: final 228 builder runs run1/run2, timestamps per probe/artifact; fixed
report date2026-10-10, random0.25, nested1440x1000, popup1440/390x1000. SHA256
and exact before/after capture times live in the outside-commit artifact
manifest. Two runs stable on semantic evidence. Chromium154.0.8037.57,
Playwright1.63.0, pdftotext/pdftoppm22.02.0. Harness uses only synthetic
SYNTHETIC-PLACEHOLDER-NOT-A-KEY. No headers/bodies/query strings recorded.

Nested: original button opens fallback from iframe; enforced CSP and sandbox
unchanged; no-key prompt and popup-blocked reset pass. ProviderCSP blocks14
observed, zero outbound/pop requests, not harness-aborted. Print Tab/Enter
calls popup print counter0->1 without an inline warning. Print throw doesn't
change opener briefError. Idempotent setup keeps 27 page stamps and 21
positioned sections, numbers ordered. Actions visible/keyboard-reachable on
screen and hidden under print media. Generator runtime purity checked.

Standalone: original generated index.html with no CSP served from separate
local static server; original button placeholder-key/failing-provider fallback
opens, paginates and prints via opener listener. Gemini/Frankfurter requests
are aborted at harness, sanitized method/host/path only, no outbound success.
Local branding/favicon404 is observed, unrelated to this report repair.

PDF uses same 227 options: A4, printBackground true, margins14/12/20/12mm,
preferCSSPageSize true, explicit print-media mode before page.pdf. Observed27
pages. All21 section titles/code/product/Dataedition/error/copyright match
227 extracted text (whitespace normalized); no print button in PDF text.
All-page word boxes lie within page bounds. Copyright is at document end.
Builder inspected final run2 page1 (Contents08/17 unobscured), page14 Technical
uses, page27 FAQ+copyright, and390 popup pixels. This is evidence for this
fixture, not clean layout for arbitrary long/AI text or native OS printing.

A preliminary harness run left media='screen' before PDF and produced50
pages, including the button; that run is rejected as PDF evidence. Final
runs set print explicitly and are the only AFTER captures used in audit.

Regressions: nestedCSV/clipboard/persistence/keyboard/mobile PASS; Finder
static PASS; offline PASS(new cache id/privacy); 198d PASS; ships226 PASS.
227 browser now explicitly skips as superseded BEFORE method; its historical
pin assertion checks REPORT227.md rather than current production source.
No claims that the older standalone feature-finder/network tests now pass.
