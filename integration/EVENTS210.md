# Events snapshot UI promotion 210

Copyright (c) 2026 Push. All rights reserved.

Dedicated collapsed, keyboard-operable Events panel reuses the same validated
geo_events response from /api/dashboard-snapshots. No route/reader/source added.
Winning snapshotsId generation alone sets the shared eventSnapshotValue; stats
refresh reads it at render time, never fetches events again. Loading/unwired/
unavailable/verified-empty/rows states differ. Count reflects actual displayed
rows, not panel.items length, whole-store count or an upcoming-event window.
Observed timestamp and event_date YYYY-MM-DD strings displayed as supplied,
never parsed through Date. Reader's 90-day window versus old dashboard 120-day
window remains explicit and deferred. Panel makes no window claim.

Server host/label policy unchanged. Client additionally requires HTTPS, rechecks
name/category/confidence/description controls and renders literal text only.
Blanked descriptions leave the row present without a description. Newlines/TAB
remain plain text; description pre-wrap and unbroken name/text wrap anywhere.
HTML strings stay inert. Client rejected rows and server rejected/truncated
notices differ. Cap100 remains. No embeds or source requests. Source links open
only on user click with noopener/noreferrer.

Generic Geo captured-snapshot duplicate removed by hiding that section in Geo;
BRICS branch preserved unchanged. Existing BRICS browser fixture was stale:
production Geo-only UI has no BRICS button. Test restores that nav only in a
synthetic HTML/JS response to exercise the preserved branch, not production UI.
Digest preview continues consuming the same server panel; no digest code edited.
No new modules/assets. Public builders reuse existing workspace JS/CSS and
public sample has no event reader/disclosure; shows source-not-connected state.

This is UI promotion only. Event ingestion, official source stub, owner-approved
source/window contract, live reader activation, data coverage and complete
events feature remain open. No event seed, calendar action, mail, DB write,
collector/bootstrap/engine change or live effects. Stored rows unchanged.
