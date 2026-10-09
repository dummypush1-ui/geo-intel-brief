# Comtrade178 publication fence

RENDER_DRY=1 returns before reads, key, network, checkpoints or output writes for
all four Comtrade bakes. This intentionally no longer tests live providers in dry
mode. No provider calls are made by source tests. Runtime key selection unchanged.

Market/marketx complete relative to the returned nongroup reporter reference;
partners complete relative to source trade-value codes; mirror complete relative
to its fixed23-country scope. Partial/failure/429 retains last-good baked output
and saves an atomic resumable checkpoint with expected/completed/missing/throttled
coverage. A successful empty API table counts as requested, not proof of healthy
country reporting. Complete relative scope is NOT universal market/source truth.
Failures>=3 no longer permanently exclude a source: retry next invocation with
existing pacing/batch limits, never a tight retry loop. Empty scope and malformed
checkpoint/reference/data fail. API count exceeding rows or100k cap refuses the
table; mirror falls back to chapter chunks and refuses truncated chapter tables.

Old market/partners/mirror state lacking v2 is reset in memory then recollected;
old trend cache lacks v3 and is refreshed. Existing baked last-good files stay
until complete scope is fetched. Outputs replace via same-directory rename, not a
cross-file transaction. Trend data is a separate complete10call/5year table; its
output may update even if partner gathering remains incomplete, never partial
trend publication. State cached only after trend output rename. No externalDB,
Git publication, provider/disclosure or workflow configuration is changed here.

Automate's two Comtrade steps propagate errors/incomplete results before the
build instead of calling every failure a skip. No-key remains an explicit skip.
Other automate steps and build readiness remain separate work. Owner decides
whether to run live bakes. Public read-only Flask pilot does not import bakes.
