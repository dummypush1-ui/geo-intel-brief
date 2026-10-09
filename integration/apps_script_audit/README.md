# Reviewed Apps Script 180 source-local audit

Strict schedule validation happens before trigger changes: exact HH:MM and
integer syntax, supported minutes/hours, weekly day, duplicate times and staging
capacity. Interval mode ignores unused DIGEST_TIMES. Only known managed handler
names are replaced. Unrelated handlers stay. Replacements are staged first;
create failure removes staged triggers and preserves the old schedule. Cleanup
failure and partial old-trigger deletion are reported for manual review. Google
trigger replacement is not transactional; duplicate timers can remain after a
delete failure. nearMinute delivery is approximate (+/-15 minutes), not exact.

HTTP 403 is visibly held in health/collection/digest/critical/weekly calls.
Non-200 responses and transport errors fail with fixed labels, no response body
or exception details in logs. No retry is scheduled. Digest acknowledgement
failure after a send reports unknown receipt state; this companion still has no
durable mail receipt gate, so a separately invoked later successful legacy cycle
can repeat articles. Legacy server mail routes remain held, and installing this
companion is NOT approved. Do not reopen them to use it.

25 trusted offline mock scenarios, one Python wrapper. Node VM mocks are not
isolation: host constructors expose process. Exact reviewed source is hash-pinned.
Only dummy fixtures, no real Google project, properties, triggers, network, mail
or deployment. Google quota/timezone/delivery and real Gmail receipt identity
remain unverified. Hash pins prove bytes, not production behavior.

Docs verified:
https://developers.google.com/apps-script/reference/script/clock-trigger-builder
https://developers.google.com/apps-script/guides/services/quotas

Historical canaries retained below describe superseded behavior, not current
trigger parsing/HTTP handling. The current structured audit is authoritative for
source-local scenarios; it is not production or receipt proof.

# Legacy Apps Script audit after P0 header migration

The reviewed source intentionally differs from the preserved original: fixed
HTTPS origin, header-only auth, redirects refused, cleanup request/trigger held.
The source pin in audit.js covers these exact new bytes. Historical send/mark,
trigger-rebuild and parsing defects remain explicit canaries, not fixed claims.
No Google script, properties, triggers or deployment was changed. Node VM mocks
are a trusted-code harness, not an isolation boundary. Companion auth tests are
in tests/legacy_geo/test_auth.cjs; seven route shapes use header credentials.
Real Google/Render behavior and migration of existing installations are unverified.

## Historical original-source audit (superseded auth transport/pin)

# Original Apps Script offline compatibility audit

Every result is offline, not production and not receipt proof. Original Code.gs unchanged. SourceSHA256 f23159b30f263e3a34cae29879900d73b23f6cf64fc6958f12712b7df484026a checked every childrun; source is preserved local copy, originating sourcecommit not independently verified here. Script compiles in NodeVM with only fake Google services, no direct require/process/fetch globals, but host-created mocks expose their host Function constructor and process via it. VM not a hostile-code security boundary; only hashpinned reviewed original code. Host Node process has normal filesystem/network powers and host mock constructor escape can expose them to original code. This is NOT an isolation or no-I/O guarantee. Only trusted exact-hash reviewed source may run; no unknown code or arbitrary scenario scripts. The escape self-test probes typeof process without I/O. child10s timeout, individualVM1000ms. Fake fetch throws on unmocked destinations/routes/responses, fake routes perform no actual requests, but no guarantee against host escape. Original routines may catch that failure, as source behavior; selftest proves directunmockedcall throws. No environment credentials loaded. Fixture addresses example.invalid and keyDUMMY_NON_SECRET only, never report them. Report logs content discarded; action kinds/counts only.

Run: python3 -m unittest tests.test_apps_script_audit, invoking node integration/apps_script_audit/audit.js. Python3.10.12/Node22.23.3.17 local scenario checks, one Python childwrappertest. Harness first hash/selftest then sendDigest cases then trigger/parsers then structuredscope report. No original Code.gs changes or Google project/properties/triggers/deployment.

Observed source behavior under fake services: empty skip, critical-only send/no mark, UTF8 fixture/order, non200/no send, truncated/replacement-decodedbad JSON throws, replacementcharacterHTML accepted, Gmail quota throw/no mark, markHTTP500 ignored with two-cycleduplicate sends, transportmarkfailurelogged, unbounded10000-IDmarkbody, allprojecttriggerdelete + partialfailure/no rollback, loose time/int parsing, dummydoGet. These are source-local outcomes, not Google/provider validation. NonUTF8 case is simulated already-decoded replacementtext, not a real Apps Script UTF8decode test.

GmailApp real no-messageID behavior and actual subjecttimezone/providerquotas/trigger limits are unverified external/API documentation questions, not proved by fake return or Utilities formatter. Source uses no receipt identity; original send-mark success doesn't establish receipt/claim policy. Open fetched-vs-displayed marking decision remains unchanged. At-least-once duplicate risk, durable atomicGeo-only claim/ledger/auth needed before delivery; no enabled sender here. Original doGet carries querysecret, not an approved publicsharing route. Trigger installer can delete unrelatedtimers, not allowed to install under this audit. Real mail/mark/collection/cleanup/deploy remain gated.

No live Apps Script connection or external API claim. Test fixtures and outputs contain only dummy values; audit script prints no recipients/URLs/keys/body/IDs. No runtime module imports this harness, no productionactivation path. Source fixture can include syntheticIDstrings, never actual DB identities.

Harness stdout is one labeled JSON line only, stderr empty on passing run. Unittest human output must be captured and prefixed offline_not_production_not_receipt_proof per physical line before publication; raw unittest output is not a report. Request mocks validate method/query/content-type and synthetic ID payload. Wrapper asserts exact17unique names/pass/sourcehash/top-levelscope and scans both output streams for URLs/IDs/addresses/dummykey. Partial-trigger-deletion failure tested.

Repro labeled stdout/stderr including child failure: python3 integration/apps_script_audit/labeled_run.py. Child timeout/failure wrapper suppresses exception details; this is display labeling, not sandboxing.
