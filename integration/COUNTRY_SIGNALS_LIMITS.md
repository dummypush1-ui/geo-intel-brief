# Country news signals (offline supplied snapshots)

This independently written module counts exact Geo country labels and existing stored risk classifications. It does not classify stories or rate countries. It does not read a database, make network requests or send anything.

28 days is a minimum observed-history threshold, not proof of complete coverage. created_at is normalized to collected_at by the existing news view. Zoned UTC collection and publication windows stay separate; invalid/missing timestamps do not fall back to each other. Future collection timestamps are excluded. Count unique article_key values in the snapshot, not distinct real-world stories. Duplicate-key rows use the first supplied row, so conflicting duplicates require upstream review.

Countries without an observation at least28 days old show insufficient_history. Older observations give observed_span_only. Neither state proves continuous collection, complete publisher/country coverage or a statistically valid baseline. Distinct active days and missing timestamps remain visible. An empty snapshot is unknown coverage, not a safe country.

Risk index and baseline stay null. A future index needs reviewed methodology, complete daily exposure/coverage metadata and country-specific baselines. A large archive or an earliest timestamp alone is not sufficient. No threat, investment, legal or official-rating claims.

Public outputs contain counts, exact country label, collection/publication window timestamps, earliest observed collection, history duration, coverage/methodology flags and unavailable-index states. They do not contain titles, URLs, database IDs or private Telegram fields. Private API/UI wiring exists (see final wiring paragraph); live source activation
and full-history coverage remain unverified.

Input is a plain list or tuple of at most10000 plain dictionaries of at most100 exact string keys each. Keys are validated before any field lookup. Larger inputs and invalid row shapes fail validation, not silent truncation. Consumed fields have length/type caps:country100, project5, article_key128, timestamp100, risk_level16 characters; exact datetime timestamps with datetime.timezone fixed offsets also accepted. Custom tzinfo and string/datetime subclasses are rejected without calling their hooks. Naive row timestamps remain missing; naive clocks reject. Unknown fields are not read or emitted. Missing fields may remain unavailable. These limits bound scan work; input parsing/transport must enforce its own byte-size limits before creating the snapshot.

The window is a closed28-day elapsed interval, including both endpoints. It can contain up to29 UTC date labels. observed_active_date_labels_in_window counts observed date labels, not0-28 calendar-day completeness. Future publication timestamps are reported separately. History display is floored to3decimal places so a sub28-day span cannot display28.0. Underflow clocks fail with ValueError.

Wired GET query labels reject400 before reading. Signal snapshot errors return503, never a fake zero. Normalized public rows are filtered to exact country and Geo before signal validation, so an unrelated country cannot invalidate that panel. The UI reports the supplied read-view row count and live-reader newest100 per collection cap; this is not28days of full history.

Operator to-do, not performed: if the Geo reader's created_at descending sort is used, inspect Atlas collection geo_intel/articles indexes and consider {created_at:-1}. The owner should be guided in Atlas one screen at a time when needed; no createIndex, DB mutation or index assertion has been made.
