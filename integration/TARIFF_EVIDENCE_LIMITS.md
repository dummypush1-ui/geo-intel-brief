# Passive tariff-document evidence preview

Independently written. Injected supplied snapshot only; no fetch/clients, DB writes, timers, ingestion or delivery. Existing default-private guard applies to UI, API and asset. Default runtime has no snapshot and returns unwired, not an empty claim of complete coverage.

A strict row keeps jurisdiction, nomenclature/edition, numeric code strings, document ID, exact official HTTPS URL, publication date, multiple effective dates, short excerpt, conditions and candidate/document-reviewed state. Review timestamps cannot exceed capture. Source-host allowlist is link safety, not proof of source authorship, legal interpretation or review. No rates/current-law verification, inferred duty change or product/origin eligibility. Supplied document-review state is recorded input; it is not agent approval and never enables actions. All display text is literal textContent.

Code digits have no invented Finder scope. Existing exact HS/HSN news-to-Finder endpoint now displays its explicit mention reason in the country page. Finder existence/context still does not prove affected legal scope. No tariff record is matched to Finder automatically.

Empty lists mean no supplied records for that jurisdiction, not no tariff changes. Unwired and failed reads are separate. View cap100, input cap1000, codes100 per row. Current official-source legal-document ingestion, terms, snapshot persistence, polling and source-review workflow remain unconfigured. Supported host catalog starts with IN/US/EU, not worldwide coverage. Publication dates are not legal effective dates. No live notification rows shipped, only browser fixtures in tests.

Official route research:
https://www.cbic.gov.in/Customs-Notifications
https://www.indiabudget.gov.in/doc/cen/cus0326.pdf
https://www.usitc.gov/harmonized_tariff_information/modifications_to_hts
https://www.usitc.gov/harmonized_tariff_information/hts/archive/list
https://taxation-customs.ec.europa.eu/online-services/online-services-and-databases-customs/eu-customs-tariff-taric_en

## Strict supplied value boundary

Exact field shape and plain string/list/None values checked BEFORE copying.
Manual scalar/list copy prevents custom deepcopy hooks. No supplied objects,
subclasses or coercion. Per-scalar max2000chars prevalidation, codes100 x12chars,
effective dates20 x12chars, then existing semantic caps. Surrogates rejected
before encoding. Normalized compactUTF8 rows cumulatively <=2MB after all canonicalization,
right before appending each row. Budget is SUM OF ROW BYTES, excluding snapshot
envelope and row separators; not full response-size cap.
not a total interpreter/input-allocation bound. Input list <=1000 still applies.

Observation/review strings<=64, aware ISO, local+UTC years1970..2100. Exact
fixed datetime.timezone clock required in view; custom tzinfo/ZoneInfo rejected
before any hook. Timestamp acceptance depends on Python version. Output ISO
format remains existing format, no new legal-date or review-authority semantics.
Plain copies on returned views remain isolated. Review_state is supplied input,
not authenticated review or permission. Host catalog only safe link restriction.

Configured17tests PASS (9existing+8plain boundary). Eight new standalone tests
cover hook nonexecution, clock hooks, mutation isolation, scalar/time bounds
and aggregate bytes. Full route tests need configured merged dependencies.
No live sources/rates/credentials/client/API/store/activation/deploy changes.

List-element UTF8/surrogates checked before copying. Returned normalized rows
now use manual plain copies, not deepcopy. Internal Python state is trusted;
hostile mutation of private _items is outside this adapter contract.

Constructor uses plain_row only: exact dict and wrong field count reject
before key iteration or set allocation, including oversized wrong-schema dicts.

Residual limits: official_url does not reject every DEL/bidi/category-C codepoint
like text() does; hostname casing is accepted through parsed hostname and an
empty port may be accepted by the URL parser. Host restriction is not canonical
exact-string identity/authentication. Caller-owned lists may change between
validation/copy under hostile concurrent mutation; no snapshot lock supplied.
Private _items is reachable Python state; view plain_row revalidates its shape
but cannot authenticate tampered semantic values. Trusted in-process callers
required; no adversarial code isolation or concurrency-copy guarantee.
