# Injected events read adapter

Historical/direct-adapter scope: statements below that composition is not
attached describe this standalone reader's initial increment. Later Geo-only
composition is separately gated and connected to digest preview; see
FEATURE_STATUS.md and GEO_EVENTS_COMPOSITION_LIMITS.md. No live schema, role,
source capability or activation has been verified by that wiring.

ReadOnlyEventsReader preserves original Geo upcoming_events query: inclusive UTC date today..today+days, event_date ascending. No database client/config/index/imported legacy module, write, collector or live route. Clock and collection explicitly injected; verified flag required. Original source: intelligence/geo/database.py upcoming_events, retained unmodified.

Caller must verify the exact collection identity and read-only credential. Production composition is not attached. Cursor query has2second server-execution max_time_ms (not an end-to-end2s deadline) and reads at most limit+1 (limit at most1000). More rows fail unavailable rather than silently truncate; complete serialized UTF-8 snapshot envelope at most2MB, each scalar16k. Collection/provider must enforce network/socket deadlines and projection before allocating payloads; this adapter cannot bound a client library's incoming wire bytes. Cursor assigned immediately after find and closed on successful read, sort/limit/max_time_ms setup failure and validation/iteration errors; close errors suppressed without disclosing details.

Only six event fields leave adapter: name/event_date/source_url/category/confidence/description. _id excluded by query, unknowns never copied even if fixture ignores projection. Zoned fixed-offset clock normalizedUTC. Invalid dates/order/out-of-window/malformed rows/surrogates/budgets fail closed. Read time is observed_at, not a claim the source announced/updated the event then. Empty verified snapshot differs from unavailable.

Display must still go through existing DashboardSnapshots reviewed per-panel public-host/label/URL gate. Reader does not establish source URL trust or open links, and is not a renderer. Source event semantics retained, but stricter shape/budget/order requirements are deliberate safety differences. Digest events and real dashboard composition remain unwired pending separate review. No source events are invented or seeded.

Budget definition is compact ensure_ascii=False UTF-8 JSON with separators(',',':'); downstream serializers must match this to retain the stated2MB transport cap, or apply their own encoded-envelope budget. Pretty-printing/default ensure_ascii output can be larger. Before any production composition, independently verify collection identity, read-only credential, client/socket deadlines and the display host policy.

Private digest preview can now consume the exact injected DashboardSnapshots Geo panel. Existing verified host/URL/text gate runs before original renderer; additionally filters inclusive UTC90day preview window. No event data assumed when absent/unavailable, and response metadata preserves observed_at/rejected/truncated/shown state. Critical/weekly do not read events. Original HTML template remains unchanged, including its700px fixed-width mobile overflow. Loopback pixels verify escaped fixture event name and source link; no external resource requests or delivery occurred. This is supplied-snapshot dry-run composition, not a production event reader or mail queue.

Digest preview metadata now counts out_of_window only within the already capped display snapshot (window_count_scope=display_capped_snapshot_only). If display panel truncates, truncation_may_hide_in_window=true: it may have dropped matching events before date filtering. No whole-source count is claimed. Preview requires a fixed aware datetime clock; injected UTC now drives original renderer date facade/header, removing server-local date drift. Original template's no-scored-news line remains when events exist but no articles score above threshold.
