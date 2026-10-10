# Served Finder network fixture (230)

Test/docs-only on landed229. Supersedes the stale browser_finder_network.py
failure recorded in FINDER-BROWSER229.md; that document remains historical.
No src/index/offline/SW/dataset/adapter/policy/provider-config change.

## BEFORE

The original script on the229 tree failed waiting30seconds for "manual
refresh only in private preview". Its verbatim timestamped log/exit1 is in
BEFORE evidence. AIS_PROXY_URL is empty. src/app.js shipsLoad4081-4142
returns proxy-unavailable before a fetch; paintShips4143+ displays "Built-in
proxy access is unavailable". AI_PROXY_URL and all built-in keys are empty.
The shared-rescue code still exists, but its configuration is empty.
The old script expected shared AIS and shared AI and therefore never reached
its later weather/AI/FX checks. No BEFORE output is relabelled AFTER.

## Current assertions

- Ships: original tab/toggle, off/on, proxy-unavailable, no fetch, no busy,
  no data, null shipsTimer. This does not prove manual AIS refresh works or
  does not work. The existing manual_ships_shell adapter remains unchanged.
- Plain words no-key: original plainWordsRun3018-3050 calls aiPickText301+
  (exact span pinned in test). It displays the unavailable error, not the
  settings prompt. Button is enabled again, no AI request. This differs from
  the no-key report button in229, which opens settings.
- Plain words own-key: existing storage seam selects Mistral. Exact POST
  api.mistral.ai/v1/chat/completions mocked success with visibly SIMULATED
  narrative, literal <b>marker</b> rather than an element, cached only in
  disposable browser storage. Separate429 checks error/no result/busy reset.
  Original model pool retries3times in this429 fixture, not3-provider failover.
- Weather: exact GET api.open-meteo.com/v1/forecast and
  marine-api.open-meteo.com/v1/marine mocked with SIMULATED fixture numbers.
  Original port selection triggers another pair. Forecast503 shows unavailable,
  data null and busy false. Marine503 leaves forecast and no invented wave.
- FX: exact Frankfurter GET /v1/2025-09-04..2026-10-09. Fixture dates/rates
  2025-10-09:80,2026-09-09:85,2026-10-09:90. The test derives12.5%year and
  5.9%month with (90/base-1)*100, then checks the original displayed arithmetic.
  This is the test's own arithmetic check, not real FX accuracy.503 sets
  V.ccyImpact='err' and removes the card, no invented rate; there is no FX
  busy flag in this original source.

Exactmethod/host/path matches only; any other external request aborts and
fails. Real outbound successes0. Mistral synthetic bearer is compared locally,
never saved. Queries, headers, bodies, prompts and keys not persisted in
artifacts/logs. Server request logs suppressed. Synthetic placeholder exists
only in test source. Runtime records method/host/path/disposition only.
No product functions/provider config replaced. A bottom SIMULATED LOCAL TEST
label added only for screenshots, not to alter behavior or security policy.

Whole SHA pins: src/app.js bcd406d75b27b053fc5716d141ca278932115f14e39eca74d19a2284fc59d313;
index.html e2ed3326bfb8ca0805677e026438ff412611eef712526dea17b49d6c7fa30625.
Exact news_api/shell/finder_network hashes in browser PINS. Exact shipsLoad,
aiPickText,plainWordsRun and config span hashes in test_finder_network230.py.
In-memory mutations of each proxy/built-in key and unavailable branch fail
loudly, without touching product files.

CSP origins checked in served browser response. Opt-in cases have zero
unexpected securitypolicyviolation events across navigations. Separate unit
checks defaultOFF self-only, unauthorized403 even with opt-in, and other news
pages' unchanged CSP. No CSP/sandbox relaxation. The negative CSP permission
check is separate from the local mock routing and is not a real-network test.
Playwright readiness uses function expressions, not string predicates that
would require unsafe-eval. No sleeps or60second waits; dynamic loopback port.

## Evidence / limits

Two consecutive final browser runs semantically equal excluding timestamps
and artifact hashes. Frozen1791576000000/Math.random0.25/AsiaKolkata;
1100x900 and390x900. Chromium154.0.8037.57, Playwright1.63.0,
Python3.10.12. Final AFTER run times and per-artifact hashes in result.json.
Final390success/plain/FX/ships/weather and error-case pixels inspected.
Desktop plain/FX/weather pixels inspected in preceding semantically-identical
run; final390 contact sheets inspected again. This is not arbitrary longAI
layout or native device/browser coverage.

Mobile limitation found, not fixed: weather table values are clipped at
initial horizontal scrollleft. Programmatic scroll moves it to the opposite
edge but beginnings/rowlabels then lie offleft. Opposite edges appear in
separate screenshots, not all values together. No keyboard accessibility or
whole-value readability claim. Outer page has no horizontal overflow; that
alone is not enough to claim full mobile readability. Bottom test label may
cover the bottom of a viewport capture; it is not product UI.

229/228/nested/static/offline/198d/ships226 final-source regressions PASS.
Default wrapper explicitly SKIPs unless RUN_FINDER230_BROWSER=1; missing
Chromium/Playwright explicitly SKIPs, never implies browser PASS.
Run `python tests/browser_finder_network.py`; FINDER230_OUT sets artifacts.

Not proven: real weather, real FX accuracy, real AI, provider availability,
three-provider failover, manual AIS availability. No live accounts, DB
reads/checks/writes/creation, sends, activation or wiring. Full project remains
incomplete. Historical feature-status claims are not silently rewritten.
