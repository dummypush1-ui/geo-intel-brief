D4: same-admitted-page title/source context for reported-code coverage

Status: review candidate, default OFF, not activated or pushed.
Baseline: 761f8f5657187f994f200db23c78dc55770f607c.

PUBLIC_CODE_NEWS_SOURCE_CONTEXT_ENABLED=false. Exact true requires the existing
reviewed live news read, full-page source binding, coverage API and coverage UI.
Preview-only composition rejects ON. The existing binding review remains needed.

ContextBroker extends the bounded coverage broker without another source read.
Each matched article receives only Geo project, title (2000), source label (200),
and absolute HTTPS URL (2048) from the same admitted parent page/carry. Missing,
invalid or conflicting context is an exact unavailable object. Raw database IDs,
private provider fields and summary are not added to the coverage response.
The response validator is closed, delegates relationship/cursor checks to the
existing closed validator, and checks the new context separately. The served
UI copy renders through textContent and creates only validated HTTPS anchors
with noopener/noreferrer. Source scripts and preserved catalogue are unchanged.
Both coverage and Finder-navigation UI variants are pin checked. No persistent
historical title cache, article-hash lookup endpoint or external request exists.

Unchanged limits: 25 matches per response, parent pages of at most 100 public
rows, at most 20 pages/2000 rows per manual scan. Existing shared cursor/TTL,
quota, replay and cleanup behavior is inherited. Expanded reply has the same
520000-byte pretoken ceiling and final 524288-byte wire ceiling. OFF retains the
existing broker and validator. Existing normalized news and Finder routes stay
unchanged. Generic source URLs are not proof of source reliability or accuracy.

This is explicit code-mention coverage, not full semantic commodity links, legal
classification, duty advice, current official catalogue evidence, or full old
news search/export. Catalogue snapshots are preserved, not refreshed. No source
credentials, spend, public activation or cutover is authorized by this module.

Verification: focused unit tests and local actual broker/browser fixture.
Browser evidence is synthetic only: no database, provider or external requests.
At 320/390/1100px the house layout, source links, wrapped title/key and caveats
are checked. Literal malicious HTML is rendered as text, not markup. Continuation
uses the existing carry; malformed response cannot produce a source link.
