# Item11 normalized date projection (202)

Pure supplied-row adapter for landed193. Original geonews database.py stores
created_at as awareUTC isoformat strings and sorts published strings; original
email_report.py selects unsent rows then score-filters. Current merged193 instead
requires explicit published OR created_at policy and normalized chronology.
Read original live source before this unit; no original queries/send paths changed.

Accept exact zoned extended ISO timestamp strings (seconds, optional3or6fraction digits,
Z or valid fixed offset), or exact datetime with fixed datetime.timezone.
Emit UTC ISO with six microsecond digits. Naive dates, dates without time/offset,
custom timezone callbacks, unknown -00:00, invalid normalized offset components,
missing values and range overflow refuse. Real BSON callers must separately verify tz_aware=True with tzinfo=UTC.
PyMongo default naive BSON Date decoding
is NOT inferred UTC: caller must verify aware decoding independently. Both dates
required even for excluded/old/below-score rows; no created-to-published fallback.
This narrows accepted string spelling vs193's fromisoformat, deliberately held.

Closed supplied digest projection only;1000rows/2MiB/16ktext cap, no truncation,
extra-field dropping or receipt-derived corruption hiding. Byte cap enforced
while building normalized projection, then full unchanged193validation. Original
row identities/data remain unchanged; normalized output selection snapshot hashes
bind canonical dates, not raw date spelling/input kind. Input-kind counts reported
separately, no assertion that equivalent snapshot is identical raw source.

No client, URI/env access, Mongo query, migration, clock read, renderer, transport,
receipt store, sender, marker, scheduler or runtime mount. No default date policy;
owner policy still outstanding. All-time receipts remain supplied fixture facts,
not authenticated delivery/no-repeat proof. This unit does not clear193's actual
schema/index/explain/source completeness/snapshot/durable receipt/renderer gates.
Old collection/mail paths held, gate2/3/4 and201cunchanged.
