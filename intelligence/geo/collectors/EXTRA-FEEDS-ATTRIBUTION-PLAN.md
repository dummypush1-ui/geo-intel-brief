# Attribution plan for EXTRA_VERIFIED_FEEDS (design only, nothing wired)

Why: every one of the 8 feeds is reusable only with credit. EC is CC BY 4.0 (credit plus indicate changes). UK feeds are OGL v3 (attribution statement). Council, ECB, BIS and WTO require citing the source. WTO also asks to be informed of reuse (landing TODO below). ECB asks that modified information be stated as modified.

Data model
- Each stored article keeps `source` (the feed name, already present) plus a new `attribution` object copied at ingest from EXTRA_FEED_ATTRIBUTION: provider, licence, licence_url, terms_url, line. The existing 25 feeds get no attribution field.
- Store it with the article so CSV and old rows keep it.

Where it shows
1. Article card or list row: the `line` text as small secondary text under the headline, with the licence name linked to licence_url (EC, UK).
2. Article detail view: provider, source, licence link, and an "Original article" link to the item URL.
3. CSV export: two added columns, `attribution` (the line) and `licence`. The existing 12 columns are unchanged.
4. A "Sources and licences" section or page listing the 8 providers with terms_url and licence, linked from the footer.

Rules
- All lines start with "Source:". Lines contain only what is true of every row. If wiring ever shortens or rewrites summaries, add a modified-text note then, not before.
- Never remove or hide the attribution line, including in dark mode or print.
- Attribution is data, not code credits.
- ECB: keep headline, link and date only. The ingest rule is in EXTRA_FEED_INGEST_RULES (drops summary, body, full_text). It must be enforced at ingest in the wiring phase with a test. The feed carries named-author speeches and interviews, and the ECB terms restrict reprinting author-named documents.
- UK: the line carries the OGL sentence. Do not reuse items that state other rights holders.

Landing TODOs (before wiring)
- WTO: the terms ask that the WTO be informed of reuse. The owner has to send that notice. It has not been sent. Do not wire without noting this.
- EC: confirm the Press Corner feed items carry no item-level copyright exclusions.
- Add the ECB ingest test: ECB rows contain no summary, body or full text.
- Re-run all 8 through strict publication_date() before wiring (last run: all verified).
- Wiring changes rss.py, so the collector113 and collector130 sha pins and the manifest/AST entries move. Coordinate the landing order with main.
