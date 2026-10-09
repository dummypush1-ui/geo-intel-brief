# Finder nested report diagnostic ledger (227)

Test/docs only. No production source, policy, sandbox, mount or activation changes.
The indexed preserved Finder source is src/app.js, SHA256
`f8ecf57f73c28c376c4508f2ce7315f3ffad0a8a26d925a9782db6bb53e38f91`.
The older FINDER_PARITY_PLAN.md rows 31 and 60 remain open, with this ledger
adding narrower observations rather than declaring report parity complete.

## Claim ledger

| Claim | Status and scope |
| --- | --- |
| Nested original report button opens fallback report | Verified in Chromium's nested private workspace fixture, with a synthetic placeholder own key. Existing CSP blocks the provider before a request reaches the harness. Original button opens an about:blank-written popup whose opener is the nested Finder frame, with source-parsed 21 ordered sections, original product title/code 090121, Data edition date/error note, and original busy-button reset. Not an AI narrative report. |
| No-key report button | Verified: original key prompt appears; no popup opens. No-key static report by button is NOT supported by this original gate. |
| Popup blocked | Verified with a harness-only window.open returning null: original popup-blocked message appears and original finally path resets the button. |
| Chromium page.pdf emulation | Captured, text extracted and pixels inspected. NOT clean layout parity: fixed footer overlaps the contents boundary on page 1; original pagination effects absent. Native print/PDF remains OPEN. |
| Popup print button invokes window.print | OPEN, observed blocked. Keyboard activation of original inline onclick leaves instrumented counter 0 -> 0 and logs enforced-CSP violation. Control test-only listener increments 0 -> 1 without a new violation. Earlier preliminary counter-1 result is not evidence of working original print. |
| Native OS print dialog, real AI narrative popup, Safari/Firefox, live network | OPEN; not tested, not implied. |
| Inline popup report script/pagination | OPEN, effect absent: zero .pgnum elements and zero inline-positioned .tpl-sec sections. Source load script would create both. No assumption that missing effect is explained solely by a console message. |

The provider fetch was blocked by the existing connect-src 'self' CSP before
any request reached the harness; harness recorded zero outbound requests.
No outbound request succeeded. Two runs observed 14 provider CSP console
blocks. That count is evidence, not a general service retry guarantee.
Existing Frankfurter attempts are also blocked by current CSP; no network is
turned on. Popup itself recorded no requests. No headers, request bodies or
query strings are saved; console URLs are reduced to scheme/host/path.

## Original seams and policy

- src/app.js 104: aiAvailable reads V.apiKey, proxy and built-in keys.
- 191 and 742: original hsn-gemini-api-key localStorage own-key seam.
- 2232-2510: original report generator, escaping, ordered section inventory,
  date, Data edition error note, inline print handler and load script.
- 2512-2525: original openTemplateReport and popup-blocked error.
- 3441-3451: original no-key gate, popup opening and finally reset.
- integration/ui/workspace.html line 5: actual iframe sandbox is exactly
  `allow-scripts allow-same-origin allow-downloads allow-modals allow-popups`.
- integration/news_api.py 52-60: actual enforced Content-Security-Policy,
  not Report-Only. The test compares exact workspace CSP and nested response
  CSP, including inline hash values derived from actual response bodies.
  connect-src remains 'self'; no extra sandbox flags or CSP directives.

Synthetic own key is only `SYNTHETIC-PLACEHOLDER-NOT-A-KEY`, set before load
in throwaway browser storage. No real keys, users, rows or service accounts.
No product function instrumentation, fake report HTML or provider response.
Harness-only print counter and window.open-null probe are labelled above.
The print control listener is attached only after the original probe, outside
production. Screenshots/PDF depict this diagnostic report, not live research.
The report's source claims about data accuracy and busy services are original
text, not verified current facts. In this run the actual failure is CSP.

## Determinism and artifacts

Date constructor/Date.now frozen to 1791576000000 (report shows 2026-10-10 in
Asia/Kolkata). Math.random fixed to 0.25. No timed sleeps. Nested viewport
1440x1000; popup captures 1440x1000 and 390x1000. Two stable diagnostic runs.
Chromium 154.0.8037.57; pdftotext/pdftoppm 22.02.0. Playwright version is in
the review receipt. No after/before-fix claims: there is no production fix.
Per-run probe.json labels capture times, viewport and selected PDF pages.

PDF parameters: A4, print_background true, margins top14/right12/bottom20/
left12 mm, prefer_css_page_size true. This is Chromium emulation, not an OS
print dialog. 27 pages observed; source-derived section titles all appear
in extracted text. First/middle/last sections were checked in text. First,
middle and last PDF pages inspected as pixels are 1,14,27. Page14 is Technical
uses; page27 is FAQ. Page1 contents meets the fixed footer, so vertical layout
cleanliness remains OPEN. All 27 rendered pages are 707x1000; a rightmost
25px dark-pixel check is zero across them. That right-edge check establishes
only empty right margins, not absence of vertical overlap or full parity.
The PDF shows the report as rendered without the pagination script's effects.
Artifacts remain outside the commit.

## Run

`python tests/browser_finder_report227.py` writes to REPORT227_OUT (default
/tmp/report227-review). The unittest wrapper is opt-in with
RUN_REPORT227_BROWSER=1; missing Chromium, Playwright or PDF tools produces an
explicit skip, never a popup/PDF pass. Source pin/policy tests run by default.

Existing nested CSV/clipboard/print-invocation and 198d browser results belong
in the receipt, with failures and any test-navigation correction disclosed.
The nested shortlist print counter is not proof of this popup's print handler.
No DB reads/checks/writes, mail/send, production assets/mount/wiring/activation,
217/201c, sender222 consumer, cutover, recipients or wording selected.

## Regression findings on the current 226 base

The unchanged nested shortlist browser script failed: current workspace opens
on Geo and it waited for hidden #d-fav. This was pre-existing, outside the root
suite; earlier CSV/clipboard proof was an earlier run, not today's current
verification. 227 makes only two actual Finder-navigation clicks after goto/
reload in that existing test. Assertions, fixture and final pass line remain
unchanged. Corrected nested script PASS, including CSV/clipboard persistence,
keyboard scroll, instrumented shortlist-print invocation and mobile width.
The original FAIL log and corrected PASS log are retained separately.

Additional current browser probes: 198d PASS; ships226 PASS; Finder static
PASS; Finder offline PASS. Standalone browser_feature_finder FAIL waiting for
popup with no own key, not a Geo navigation issue. browser_finder_network FAIL
waiting for manual ships refresh text, not a Geo navigation issue (direct
Finder route). Neither is changed here, neither counts as current parity
proof. These failures are retained and require separate scope if repaired.
All other browser_*.py workspace-entry scripts were scanned for this exact
Finder-hidden assumption; the nested script was the affected Finder test.
News-only/map/weekly/country/channels scripts are not report evidence and
are not claimed rerun by this unit.

2026-10-10: 228 supersedes current source/snapshot pins and popup behavior. The observations and source hashes above remain historical BEFORE evidence. See REPORT228.md.
