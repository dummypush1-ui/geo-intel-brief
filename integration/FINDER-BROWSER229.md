# Current own-key Finder browser regression (229)

Test/docs-only. Changes: browser_feature_finder.py, test_finder_browser229.py
and this document. No src, snapshot, provider configuration, policy, SW,
server route, dataset or 228 historical test/doc changes.

## Why the old test failed

The BEFORE script expects a configured shared hsn-ai-proxy chain and Mistral
fallback with no own key. Current source has AI_PROXY_URL and all built-in
key strings empty. The shared-rescue code is still present, but its config
is empty; this is not a claim that the shared-rescue code was deleted.
No-key original d-tpl opens settings and returns before window.open. The
unchanged script consequently times out waiting for a popup on the 228 tree.
Timestamped verbatim failing log and exit code are BEFORE artifacts outside
this commit. AFTER captures come only from the final corrected runs.

Current exact pins:
- src/app.js bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313
- index.html e2ed3326bfb8ca0805677e026438ff412611eef712526dea17b49d6c7fa30625
- ownProvider exact span SHA256 43bc397649b5d507858b9633f59b58815ae363f3ee7ac414ea39060b619b217e
- aiReportText exact span SHA256 95dc3562eaa83a65c957fb38f6019c9e786db3592686e4d5d288c67f9b37ee11

Span delimiters are in the unit test; any drift fails loudly. Empty shared
config and existing own-key dispatch are asserted in source and browser.
The existing prepare_shell adapter remains unchanged.

## Narrow proof

1. No-key: original button displays key prompt, opens no popup.
2. Mock success: original own-key storage seam selects Mistral; only actual
   api.mistral.ai/v1/chat/completions is handled. Synthetic narrative says
   SIMULATED TEST TEXT and is not a verified AI answer. Original button opens
   AI-assisted edition; HTML-like marker is literal text, not a b element.
3. Mock 429: separate fresh context, original provider failure opens the Data
   edition/error note and resets busy button. No shared-rescue claim.
4. Original popup opener listener invokes instrumented print counter1 and
   page-number setup completes. Actual OS print dialog not tested.
5. Three-provider UI enumeration is an enum check only. Unknown NVIDIA saved
   provider refusal yields no new request. Neither proves three-provider
   failover or any real provider's availability.
6. Retained bounded-body timeout probe patches fetch/timers only within its
   isolated test call and restores them. It is instrumented helper proof,
   not a real provider timeout or a change to product code.

Synthetic key is checked in memory against the obvious placeholder, never
saved in runtime artifacts. Prompts, headers, bodies and URL queries are not
logged/saved. Logs contain only method/host/path and fixture disposition.
Frankfurter reads are expected aborted reads, not FX accuracy evidence.
Any other external host/path aborts and fails the test. Real successful
outbound requests are zero. Mock fulfillment is local Playwright routing,
not a network call. No provider, AIS proxy or production network is enabled.

## Evidence and run

Two consecutive final runs have equal semantic results/calls; report date
2026-10-10 from frozen clock1791576000000, Math.random0.25, Asia/Kolkata.
1100x900 and390x900 popup captures are timestamped in result.json. No sleeps;
wait on source UI conditions and report document completion.
Chromium154.0.8037.57/Playwright1.63.0/Nodev22.23.3/Poppler22.02.0.

Success and429 PDFs both observed26 pages, A4 printBackground true,
14/12/20/12mm margins, preferCSSPageSize true, explicit print media.
Builder viewed final run2 pages1/13/26 for both, plus both390 screens.
Contents are readable; middle success page shows simulated text with literal
markup; final FAQ table and copyright fit. This does not establish layout
for arbitrary long real AI responses. Runtime artifacts remain outside the
commit, with SHA256/timestamp manifest. No BEFORE capture is relabelled AFTER.

Default unittest explicitly SKIPs the browser without RUN_FINDER229_BROWSER=1
or without Chromium/Playwright/PDF tools. It never implies browser PASS.
`python tests/browser_feature_finder.py` is the explicit browser command;
FINDER229_OUT chooses the artifact directory.

Rerun 228 browser, nested CSV/clipboard, static, offline,198d and ships226 PASS.
Existing browser_finder_network.py remains FAIL: it expects a shared AIS
proxy/manual-refresh result, but original AIS_PROXY_URL is empty and ships
returns proxy-unavailable before a fetch. Its current failure log is retained.
That script is a separate 230 candidate, not changed or silently skipped.
Full project and real-service/activation parity remain incomplete.
