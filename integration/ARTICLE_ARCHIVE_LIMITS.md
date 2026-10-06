# Private supplied supported-schema archive, not durable backup

This module only packs, unpacks and retrieves supplied records in memory. It
has no source reads, files, routes, writes, uploads, delivery, deletes or marks.
The original RSS and GNews save paths store summary[:300], not full body/raw
text. MongoDB adds _id and created_at ISO text; later updates add Telegram
references and emailed bool. No full-history or actual Atlas-schema claim.
BRICS has a different SQLite contract and is not supported here.

The schema is synthetic_supported_geo_storage_fields_v1. Source excerpts with
line numbers and full-file SHA256 are in the review evidence. They support
field/type selection, not a verified live collection or source completeness.
Unknown fields and any nested containers under producer fields are refused.
Text fields must be exact str (up to 1M characters before aggregate bounds),
score finite exact int/float within +/-2^53, corroboration exact int in the
same range, emailed exact bool, telegram_message_id int64 or None, and _id
ObjectId or nonempty string up to 100 characters. These are bounded supplied
fixture types, not a claim that every value follows the original producers'
semantic ranges. Text can contain private content. This rejects unknown
private fields, not secrets typed into a supported text field.

The independent tagged-array codec supports builtin bool/int64/finite float,
str/bytes/ObjectId/null/dict/list/BSON-like UTC millisecond datetime. That
broader codec is NOT the producer-field exclusion boundary. Codec depth 8,
20k nodes, dict 30/list 100/string or bytes 1M; no subclasses or hooks. BSON
fixed-offset datetime normalizes to UTC, naive assumes UTC; original offset
and naive flags not preserved. ISO producer text remains exact. Non-ms
microseconds refused. Missing fields and explicit supported null preserved.

100 records and 2MiB final encoded archive. Capture checks a conservative
aggregate budget during each field and each character BEFORE tagged copies.
It adds 192 + key length per field and at least six bytes per character,
reserving 4096 bytes for the envelope. This covers UTF-8, JSON escaping, tags,
identity manifest and scalar overhead without a large UTF-8 temporary. It
stops on first overrun and shares a 20k encoding node cap across records.
It may refuse archives below the final byte cap. Final bytes also checked.
No base64/bytes values enter producer capture. Decoder checks bytes before
JSON parsing, then validates all records and manifest before returning any.
The JSON parser can allocate within the 2MiB input limit before typed checks;
there is no hard parser CPU/allocation guarantee.

Order and typed identity preserved. Exact duplicate rows kept; conflicting
same identity refused; duplicate identity retrieval is ambiguous and refused.
Closed version/schema/scope/count/manifest/ordered records and UTC creation
stamp covered by SHA256. Hash is integrity, not authentication or source
proof. Only supplied_subset or supplied_truncated_subset; neither means full
history. Private IDs/URLs/content remain private archive bytes. No public
news/CSV/mail/preview wiring. Pack is not durable storage or cleanup approval.

V3: 10 focused tests pass, including nested private fields, multibyte and
many large records, stop-before-tag-copy, typed int64 Telegram ID, separate
codec roundtrips, duplicates, aliasing and corruption. No live DB operation.
