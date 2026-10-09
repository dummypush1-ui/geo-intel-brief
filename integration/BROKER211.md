# 211: two unselected broker body parsers

This closes the body parser for finder198 + native201 only, not every
historical broker parser and not Finder-proxy-complete. No live effect.
The third copy of the old parser remains in replay199_broker, behavior unchanged:
malformed/extra-field JSON gives 409 there. It is synthetic-only/unselected;
if ever selected for use it needs its own reviewed unit first.

Both changed handlers call the same pure broker_json211.parse after existing
account, session, Origin and CSRF guards. No auth change. Direct non-POST or
unknown route returns 404 without body reads. The existing auth wrapper rejects
broker query strings with 403 and unsupported methods with 405. Standalone
parser query rejection is 400, defense in depth for direct calls only.

Raw Content-Type must be application/json (case insensitive, surrounding space
accepted) with at most one charset=utf-8 parameter (unquoted, case insensitive).
No other parameters, JSON suffix media, or declared transfer encoding accepted.
Raw Content-Length must be positive ASCII decimal digits, no leading zeros,
whitespace or signs; bounded before integer conversion. Missing/empty is 411.
Strict UTF-8 without BOM, duplicate decoded keys, non-finite values, top-level
non-objects, JSON decode/value/Unicode/recursion errors are refused with 400.
Duplicate escape-equivalent keys are also refused. No raw body is echoed.
Unexpected internal errors remain generic 503, not malformed-input errors.

Nonce is exactly the engine's 20..80 ASCII letters/digits/underscore/hyphen.
Model identifier is exactly its 1..100 ASCII letters/digits/dot/underscore/slash/
hyphen rule. Gemini-specific slash/catalog admission remains in the engine.
Only gemini/groq/mistral and fixed server-built payloads exist. The model catalog
is still empty. Ships port is a 1..100 safe string; membership stays engine-only.
Prompt is 1..8000 Python Unicode code points, not UTF-16 units; TAB/LF/CR allowed,
other C0, DEL/C1 controls and all surrogates refused. Provider payloads,
URLs, headers, messages and tools are never caller-supplied.

The raw cap stays 16384 bytes and is checked before parsing. It applies before
8000-code-point prompt admission: 8000 ASCII characters fit, but a three-byte
UTF-8 prompt reaches the cap around 5400 characters (exactly depending on the
other fields/spacing). JSON Unicode escapes use six raw bytes per BMP character.
Astral characters are one code point and four UTF-8 bytes. Engine-generated
payloads retain the separate existing MAX_REQUEST_BYTES limit and held409 path.

## Deliberate behavior changes

- Media mismatch remains 415 json_required; stricter raw parameter checks now
  reject media parameters previously discarded by req.mimetype.
- Declared/raw oversize remains 413 request_too_large.
- Missing/empty length changes 413 request_too_large to 411 length_required.
- Zero, signed, spaced, leading-zero or invalid length becomes 400 invalid_request
  (zero formerly413; Werkzeug formerly normalized some noncanonical forms).
- Short read remains 400 invalid_request. Observable terminated extra bytes
  become 400; over-cap terminated bytes become 413.
- Malformed/non-conforming/extra-field JSON changes 409 broker_request_held to
  400 invalid_request; invalid nonce/model shape also moves engine-held409 to400.
- Catalog, port admission, budget, replay and transport ValueError paths stay
  409 broker_request_held. Unexpected failures stay 503 broker_unavailable.
- Existing test expectations changed only: test_finder198c extra-url409->400;
  test_native201b extra-url409->400. test_finder198a/replay199ca/replay199cc
  behavior is unchanged. All catalog/admission/replay expectations stay409.

## Limits and verification

WSGI terminated streams permit bounded extra-byte checks. Nonterminated streams
are Content-Length limited; extra bytes and repeated wire Content-Length fields
may be unobservable. This is NOT HTTP-smuggling protection. No runtime server,
production mount, UI, env, account provisioning, secret, budget/retry/refund,
receipt, provider catalog or live transport changes. Native201c remains held.
Tests compare actual engine nonce/model vectors, both handler payloads and safe
errors, raw cap/multibyte/escape interplay, framing, hostile JSON, and auth-order
stream/get_data/get_json spies. Archive199's old extra-field409 is pinned.
