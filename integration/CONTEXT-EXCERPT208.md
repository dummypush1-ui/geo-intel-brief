# 208: visible bounded Finder description context

This changes only the merged workspace. Preserved Finder detail/index bytes,
the matcher and the unit207 server cap stay unchanged. index.html lines3647-48
render esc(pretty(e[2])) as detail-desc. pretty (928-934) changes all-caps case,
not length. The workspace previously sent the whole textContent. The actual
0:010619 description is252characters and failed the existing200term cap.

Now ONE product term is the first200Unicode code points, counted with Array.from,
without splitting a UTF-16 surrogate pair.199ASCII characters plus emoji plus tail
returns200points, including the whole emoji.150emoji count150, not300UTF-16 units,
and show no notice. A prefix may cut mid-word or mid-character sequence (ZWJ or
combining sequence). No fuller matching coverage is claimed.

There is no whitespace normalization or control repair. TAB/LF/CR/NBSP remain.
DEL/C1 or a lone surrogate in the prefix still gets400. The existing frontend
catch shows "News is unavailable. Finder remains separate.", not the raw server
body. The notice and excerpt remain visible. Error resets lastContext, allowing
later DOM-triggered replay, not automatic retries.0..2point descriptions still
send an empty terms list.

The notice and keyboard-operable details summary live in the PARENT document,
not the iframe MutationObserver target. The excerpt uses textContent, not HTML.
The notice states first200characters, full Finder description preserved, and
matching may miss details outside the excerpt. It is separate from the loading,
results and error status, so replies never overwrite it. Short descriptions,
no-code and search context clear the notice and excerpt. Full original text plus
code-point length participate in local lastContext, but never go in the request.
The existing generation guard rejects a stale long-to-short reply; long replay
still works. Code, system and country stay unchanged. Server cost is not widened.

## Static module routes

The new module is allowlisted both in news_api's private asset route and in
public_preview_builder's public-sample ASSETS. The latter was missing in the
first source candidate, which broke the static workspace.js import on that path.
That candidate was rejected. A public-preview test now checks the new module200
and an unrelated asset403. No public POST or private access is enabled.
The public sample has its existing empty-source, offline-Finder scope; this unit
does not make related-news POST available publicly.

## Test and visual scope

Pure Node checks0/2/3/199/200/201/2850, the emoji200boundary and150emoji, multiline
and NBSP, unsafe plaintext and control preservation.23focused Python tests include
workspace,207 and public-preview allowlist checks. Actual merged workspace and
preserved Finder in local Chromium at390/1280 check0:010619's exact body: code
010619, systemHS, empty country, and ONE200point term. Full252detail remains;
the real local207handler accepts the prefix. Short0:090121clears the notice.

Synthetic DOM probes cover literal <script> and &lt;,200unbroken characters,
DEL/lone-surrogate400 with a visible excerpt, error replay,150emoji and stale reply
then long replay. All requests are loopback; zero external requests/page errors.
Actual-source screenshots at390/1280 were inspected directly: readable complete
notice and excerpt, no horizontal overflow. The full Finder keeps its existing
internally scrollable frame. Screenshots do not show every Finder section at once.

No live data, accounts, providers, DB writes, mail, collectors, timers, deployment
or cutover. Original index/data are unchanged. Long descriptions now submit a
visible excerpt, not the whole phrase. Other207 bounds/control refusals remain.
201c stays held.
