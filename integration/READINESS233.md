# Repo-only readiness ledger (233)

Checkpoint: c7b231d636922958f6c81a59a0a4aa6ec74d419f.
This is source and local test evidence, not a deployed release or live
verification. No automatic live switch follows from this ledger. Open gates
below are separate from test results; this document selects no live subset.

## Landed Finder changes and evidence

The builder and independent reviewer ran the named local probes. Reviewer
verdicts and exact runs are retained in each unit's review receipt/handoff;
committed docs describe the evidence, not proof of a live runtime. The tree
hashes below are verified from git, not inferred from a report.

### 228: report popup repair

Commit dfec65891ac509405c75c3094b7a0fb836190e9f.
Tree 1a03815b400442e8a231f9ca73a631f8fc915ce8.
Sources: src/app.js (setupTemplateReportWindow/buildTemplateReport), rebuilt
index.html/offline.html, integration/REPORT228.md; probe
tests/browser_report228.py and tests/report228_test.mjs.

Changed popup inline handlers/scripts to opener-side setup under inherited
CSP; pagination and print binding work in the local simulated report fixture.
Builder and reviewer observed intercepted print calls and rendered PDF pixels.
Not proof of a native OS print dialog, arbitrary report content, real AI output,
all browsers or hosted deployment. No real runtime observation recorded here.

### 229: own-key browser regression

Commit c0db3e69f2e33a3c3652eeb215bdcf18e1b6f8c4.
Tree 6bf46d2501cb7324506bfd60a98a44adbc260e4e.
Paths: tests/browser_feature_finder.py, tests/test_finder_browser229.py,
integration/FINDER-BROWSER229.md.

Tests-only: replaced stale shared-proxy fixture with current no-key prompt,
local mocked Mistral success and 429 fallback. Builder and reviewer ran the
probe; simulated text remains literal, print counter 1, fixture PDF 26 pages.
No real provider availability, AI quality or three-provider failover proof.
No production app change and no real runtime observation recorded here.

### 230: network browser regression

Commit 88604076805e3b658773ad4a4b091b5ca8436d7b.
Tree 2eebe6fe03b54c1e4eb8e1697d0d27a07410609e.
Paths: tests/browser_finder_network.py, tests/test_finder_network230.py,
integration/FINDER-NETWORK230.md.

Tests-only: exact local mocks for forecast/marine, FX and own-key plain words;
empty AIS proxy means unavailable without fetch. Builder and reviewer ran six
simulated cases and failures; zero real outbound successes. No real weather,
FX accuracy, AI, failover or manual AIS proof. Current network preview remains
default-off (integration/news_api.py create_app, integration/finder_network.py).
No real runtime observation recorded here. Mobile clipping found in 230 was
subsequently fixed by 231, not by this test change.

### 231: weather table phone fit

Commit 7333a8ab37027fb2d265f19af82f643ed739bd93.
Tree 50f95116564d8d6761b68c516e4b2c624787dcb0.
Paths: src/style.css, integration/WEATHER231.md,
tests/browser_weather231.py and tests/test_weather231.py.

Scoped CSS fits only the successful weather table. Builder and reviewer saw
full labels/values/date/warning at 320/390/1100 light/dark with local simulated
weather, long-number stress, keyboard/select and503 states. Global 680px table
rule untouched; app, dataset and sw.js unchanged. Not real weather correctness,
all-browser proof or live availability. No real runtime observation recorded
here. Derived raw snapshots/pins changed, not a live deployment.

### 232: public offline CSV and scroll

Commit c7b231d636922958f6c81a59a0a4aa6ec74d419f.
Tree 427e0bc06b58a21fe932cdd0eb4b379935e4bd4f.
Paths: integration/finder_offline.py, integration/ui/finder-offline-sw.js,
integration/OFFLINE232.md, tests/browser_offline232.py, tests/test_offline232.py.

Offline served copy reuses existing online CSV safety and shortlist scroll
transforms before CSP hashing. Builder and reviewer downloaded CSV from the
actual cached-local page, with synthetic session notes only. Danger cells get
an apostrophe; NUL removed; quotes/CR/LF/astral Unicode survive. Six columns,
order, normal values and filename retained; normal row matches online export.
Invalid surrogate already became U+FFFD through the original Blob, so no
before/after downloaded-byte change is claimed for that row.

Builder and reviewer viewed 320 light/dark and end-scroll: Tab reaches the
named region, ArrowRight scrolls, End shows Remove fully. Builder also viewed
390/1100 light/dark; 390 fixture fits. BEFORE outer page already fit, so no
whole-page-widening claim. Raw animated keyboardScroll numbers vary (1 versus 2);
semantic success, not the raw pixel number, was stable in two runs. Session
notes/shortlist/keys clear on fresh page; offline storage writes 0. Not hosted
HTTPS/Safari/quota/spreadsheet-client proof. No real runtime observation here.

## Derived cache history, not activation

228:2491a5a38160 -> 4f48ae1b3cd7 (REPORT228.md and git dfec6589).
231:4f48ae1b3cd7 -> c100d1017b7c (WEATHER231.md and git 7333a8ab).
232:c100d1017b7c -> f08e061a1af2 (OFFLINE232.md, git c7b231d6).
232 ID is first 12 hex SHA256 of the complete served offline response, tested
by test_offline232.py. Worker logic unchanged except CACHE; existing activate
deletes old snapshot caches. This matters only on future explicit serving/use.
Raw index/offline/app/dataset/sw.js unchanged in 232. No activation recorded.

## Last-known repository gates

At c7b231d6, builder retained receipt: root 2175 =650+200+125+60+65+200+250+625,
8 skips and 1 expected failure; collectors 285, checks 10, world 26; closure 584
with 7 skips; focused 48 with 6 skips; 97 JS syntax checks including cjs. Logs are
builder runs; reviewer checked receipt sums/hashes and reran selected units,
including explicit offline232 browser wrapper 3 OK. Reviewer did not rerun the
whole root suite. Required Finder browser regressions ran on the audited
identical sources. These numbers are not evidence for a later runtime merge.
The retained 232 receipt and root1..root8/collectors/checks/world/closure/focused/
node-all logs support these counts. No live readiness follows from them.

## Remaining gates and owners

Runtime status below is runtime's own report relayed at 06:45 IST Oct10, not an
independent builder audit of a target. Runtime has no active executable bundle,
patch/image/install or target acceptance receipt. Last direct current-main
source audit at 22:03 Oct9 found runtime_build absent; later source receipts do
not establish that a bundle appeared. Recheck source before execution.

- Runtime owns 27: complete pinned bootstrap, OS/wheel/native/app artifacts,
  exact runtime_build bytes/manifest/anchor, fresh install/import proof and
  selected-runtime environment/start parity are missing.
- Runtime owns 28: supported interpreter matrix and actual target validator,
  timezone, JSON-depth, bwrap/process identity/deadline/kill-reap acceptance,
  including combined 512 MB boundary. Fixtures and 768 MB sampled monitoring
  are not target acceptance.
- Runtime owns 29: manual build scaffold exists, but required reviewed input
  package, selected current-source closure/build receipt and target identity
  are missing. No build dispatch reported.27-29 are open, not a current build.
- Runtime owns 209 target vectors: ship integration/html_text209.py and pass
  its golden vectors on the actual selected interpreter. Only 3.10.12 proven
  (tests/test_html209.py and integration/html_text209.py).
- Cross-component held 201c: later source selection plus runtime validation
  need accepted native production composition/write selection and real Atlas
  roles/schemas/admission/transactions/durability measurement, exclusive-writer
  and DDL evidence. Current source is not permission to execute writes
  (tests/test_native201guard.py, native201 modules).
- Owner owns DB URL/Render environment stage. Owner enters the connection
  setting at wiring stage. Agent DB presence checks/reads/create are not
  permitted by the latest instruction. No check performed in this ledger.
- Cross-component held 217 mount: later source unit must provide exact
  mount/selection closure, runtime must validate the target. Source-only
  Apps Script wrappers are not mounting (integration/MAIL-SURFACE217.md).
- Sender222 consumer is open: later source unit must supply actual reviewed
  runtime caller consumption (tests/test_sender_scope222.py). Runtime then
  validates it; source helper existence is not a working send path.
- Owner owns final recipients/words review before mail effects. Apps Script
  is the selected rail; sends and SMTP fallback remain held. No recipient,
  sending words or user data is included here (feature_mail_mount docs).
- Hosted accounts, trusted proxy and configuration require later source
  closure and runtime selected-target validation. Closed memory account
  fixtures are not shared-store/login/proxy readiness (integration/accounts,
  integration/FEATURE_STATUS.md accounts limits).
- Real provider/CORS availability, AI disclosure permission, polling/collector
  activation and hosted PWA remain open. Runtime/later source units must
  establish exact configured routes and capabilities; owner must approve
  disclosures and activation. Local simulated fixtures above do not prove
  live availability (FINDER_PARITY_PLAN.md and FINDER_OFFLINE_LIMITS.md).
- Owner still chooses actual compute target and intended live subset after
  the readiness package is known. Runtime must establish selected release/
  deployed identity, current merged smoke, exact flags, one scheduler owner,
  rollback/backup proof and no duplicate writers/sends. Final specific owner
  choice plus per-step confirmation remains necessary. No automatic 09:00
  switch or blanket go/stop recommendation is made here.

Full project parity is not established. Static Finder function coverage remains
partial (tests/browser_finder_static.py covers code details/favourites/CSV,
not the whole feature inventory). The two current parity-plan rows supersede
popup/offline caveats only; other open rows are retained.
