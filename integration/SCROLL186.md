# Geo feed scroll loading (source only)

The whole-store pager185 must be wired behind its default-OFF flag. Server HTML
emits a true marker only for that adapter; otherwise existing /api/news loaded100
mode stays unchanged. No UI request can turn a reader flag on. New module is same
origin and added to existing approved static asset allowlist. No new live hosts.

Scroll near the bottom requests25 more, with Load more as keyboard/manual fallback.
No refresh timer/polling. Sequential requests only; filter/sort/refresh aborts and
invalidates old replies before JSON/render. Leaving Geo cancels the old generation.
Empty filtered scan with cursor is not EOF: button can continue. EOF stops loading.
409/429/other errors pause; already visible cards remain. Manual refresh starts
again. Network abort doesn't close the backend stream immediately:185expiry reclaims
it. Repeated fast resets may hit16streams/429 until expiry; no silent retry loops.

Live DOM limited200cards with removal notice and height compensation. This is a
DISPLAY WINDOW, not a traversal cap. Earlier cards are unavailable for backscroll;
refresh begins again. No all21kRAM/DOMload. Browser position may shift for late font
changes/margin collapse; no claim of pixel-perfect virtual-list caching. No total
count fabricated. Raw-source sort/mutable-read meaning comes from185API. Existing
summary charts/exportCSV remain latest100 sample, not full database summaries.

Existing safe card rendering uses textContent/validated URLs. Controller checks
public response scope, mutable-read marker, ≤25items and43char opaque tokens;
source data still governed by185sanitizer. Public Finder actions remain suppressed
by existing serving transform. HOME Geo layout/theme/navigation stays intact.

Tests: pureJS sequential/abort/stale/EOF/empty/error/schema paths; server markers,
OFF/default/public static module routes; local Chrome fixture scroll beyond100,
200card trim,390px no overflow,409preserves cards,refresh reset,tab-switch stale.
Screenshots of desktop/mobile/expired states inspected. This is fixture evidence,
not a live Mongo/index/worker-route or production performance claim.
