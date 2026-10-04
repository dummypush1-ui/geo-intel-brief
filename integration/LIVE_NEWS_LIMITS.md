# Live news preview UI

The old separate news tab is removed from the workspace UI only. Preserved
source, project identities and API filters remain intact. Geo news is still
the Geo read view, not a union of all stored project articles. No migration or
silent policy change is performed by removing a tab.

Five seeded fixed video IDs are copied from source configuration. Availability
or current live status is not guaranteed. Mini players and selected large
player use youtube-nocookie embeds, muted autoplay and inline playback.
Browsers may block autoplay and broadcasters may disable embeds or end a video.
External watch links remain available. Opening Live news first creates players;
loading the workspace alone does not contact YouTube. Multiple concurrent
players use data and duplicate playback of the selected video is intentional.
No live-discovery polling, YouTube API key, message listener or wildcard trust.
An ended-state overlay is not implemented; YouTube owns its player UI.

My channels stores up to20 named video IDs in browser localStorage only. It does
not change original config, DB, GitHub or Render disk. It is per-browser, not a
cross-device durable store. Clearing site data loses changes. Storage failure
is explicit and leaves page-session settings. Cross-device server persistence
requires a separate reviewed destination and owner approval. No such adapter
is wired. Accepted inputs are bare11-character IDs, exact www.youtube.com
watch links and youtu.be links without extra params. Channel/live-page links
are deliberately unsupported rather than guessed into video IDs.

Names and errors render as text; no innerHTML. CSP extends only workspace
frame-src to exact youtube-nocookie host. Existing Finder CSP stays separate.
News refresh/theme never call player rendering or change player frames. Channel
edits may recreate players; selection changes only the large player.
No auto-news timer, collectors, mail, DB writes or deployment are enabled.

Embed iframe sandbox is allow-scripts allow-same-origin allow-presentation.
Real-network playback and CSP behavior remain unverified; fallback links stay.
Add/remove while Live is hidden updates local settings/list without creating new
players; retained mini frames keep their DOM identity. Removed channels may
remove their own frame. Switching back reconciles additions/selection. Existing
dead other-project UI branches remain in workspace.js pending later cleanup;
no separate tab activates them. Oversize saved lists explicitly fall back to
defaults. Per-device localStorage is a prototype, not final server persistence.
