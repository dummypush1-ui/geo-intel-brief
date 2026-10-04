Copyright (c) 2026 Push

# weekly_report (offline weekly intelligence PDF)

Pure module with its own PDF writer. No network, database, application-file or settings reads, no clock reads, no sending or scheduling, no third-party runtime dependency (Python standard library only). The only outside read is the standard library's time zone lookup (zoneinfo reads the system tz database). The caller supplies rows and timezone-aware datetimes and gets PDF bytes back. Same input gives identical bytes; environment variables do not change output (tested, including SOURCE_DATE_EPOCH).

## Interface
- `build_weekly_report(news_rows, tariff_records=None, *, period_start, period_end, generated_at, display_tz="Asia/Kolkata", title=...) -> bytes`
- `summarize_week(...) -> dict`, `render_pdf(summary) -> bytes` (the renderer re-cleans every text, number and link in the summary it is given; only https links become PDF links)
- `sanitize_news_rows(rows, period_start, period_end, generated_at) -> (rows, stats)`
- `sanitize_tariff_records(records, generated_at) -> (records, stats)`
- Datetimes (including those in a summary passed straight to `render_pdf`) must be timezone-aware and between years 1970 and 2100 (ValueError otherwise). Period is [start, end) and must be 1 to 31 days long (ValueError otherwise); the per-day table lists every day of the period, never cut.

## Closed field lists (everything else is dropped, never echoed)
News: article_key, project, url, title, summary, source, original_country, category, published_at, collected_at, risk_level, credibility, score, corroboration_count.
Tariff evidence (own list): record_id, country, product_code, measure, rate_text, effective_date, source_name, source_url, captured_at, note.

## Rules enforced
https links only (scheme normalised to lowercase; only the default port, or :443; no credentials, backslash, spaces, control/invisible chars, non-ASCII, over 500 chars); dates need an explicit offset (naive, overflowing, over-long or out-of-range rejected and counted); items after generated_at or outside the period are excluded and counted; duplicates dropped; bool/NaN/inf and numbers beyond 10^12 rejected; text is first limited to 8 times its cap, then normalised, then cut to its cap, so huge input is cheap; input capped at 2000 news rows / 300 tariff records with the cut shown in "Data checks"; 25 top items and 60 tariff rows listed.
Risk labels and scores are printed as supplied; nothing is scored or inferred. Dates always show the zone, e.g. "05 Oct 2026, 08:00 IST (UTC+05:30)".

## PDF writer (_pdf.py, _render.py, _metrics.py)
Own code. 390 x 780 pt pages (a fit-to-width view on a 390 px phone is 1:1; smallest font is 9 pt, body 11.5 pt). Base-14 Helvetica and Helvetica-Bold, WinAnsi, not embedded, so no font files and no font licence in the product. Text outside the Western European set prints as "?" (stated in the report). Line widths come from `_metrics.py`: advance widths measured offline from a metric-compatible font; plain numbers, no font data. Metadata: Creator/Producer "Copyright (c) 2026 Push", creation date = generated_at; each page footer carries the same notice.

## Port note (Python and platform)
Needs Python 3.9+ for zoneinfo. On Windows or minimal images with no system tz database, install the `tzdata` package (free) or the time zone lookup raises. No other runtime dependency, nothing to pin. Test-only: `pypdf` (tested 6.x), optional `pikepdf` (structure check); keep these out of requirements.

## Not done / for Builder A
No route, button, schedule, mail or storage; wiring and where rows come from are A's. Fixture data only in tests. Not checked on a physical phone or in every viewer: checked with pypdf (strict), pikepdf/qpdf, poppler render and a visual look at every page.
Run: `python -m unittest discover -s tests/weekly_report -t .`
