# Requested features awaiting implementation

## Story sources list

Recorded October 6, 2026, from the user's feature request and refinement relayed
by the parent. Status: requested, future increment after the current queue.
Do not build yet.

### One news page: main story and similar reports

User example: channel X reports "Tomorrow rain". That is the main full record.
Another 2-3 channels may cover the same story with different, extra or minimal
wording. Those reports must NOT become separate full news records.

On the same news page, show the main story's full data. Below it, show a
"similar" section listing each other covering channel's name, short wording
and link. Save the per-channel source/title or short wording/link/time so the
other links and mini data survive grouping. This is the user's "Full coverage"
idea, refined to one main record plus a similar-reports list, not duplicate
full pages for each channel.

Matching the same story across different wording is the hard part. Future work
needs title/content similarity, not exact-title dedupe. A related topic is not
necessarily the same event; matching accuracy and false-grouping cases need
review before implementation is treated as correct.

### Current gap

intelligence/geo/processing/dedupe.py keeps one near-duplicate article (first
seen, or the higher score when score_key is supplied), increments corroboration,
and drops the other articles' source details and links. It uses fuzzy title
similarity, not title/content story matching. The count is matching records,
not a verified count of distinct independent channels.

No grouping/schema/storage/UI code change is included in this record. Preserve
source identity and per-channel mini data; do not assume the existing count is
a sources list. Main-record selection and similarity rules remain future design
work, not an instruction to change the original collector now.

## Anti-hacker layers

Recorded October 6, 2026, from the user's request relayed by the parent.
Status: queued after current work, alongside the integrated serving/security
review package. No implementation or activation now. Free/simple only, no
paid services.

Requested scope:
- Rate limiting on endpoints.
- Input validation review.
- Honeypot: hidden form field and fake admin endpoint that auto-flags/blocks
  bot IPs.

Future design must review trusted-proxy/client-IP handling, shared rate-limit
state, validation boundaries and abuse tests. Honeypot-triggered blocking
needs false-positive, shared-IP, expiry/recovery and accessibility review;
an endpoint hit or filled hidden field alone is not proof of a hacker.
Do not treat these layers as a complete security guarantee. No real IP
blocking, endpoint addition or configuration change is included in this note.

## Login security verification

Queued with production login wiring: verify password persistence uses a salted
password KDF (bcrypt/Argon2 or equivalent), never plaintext, and verify actual
HTTPS responses set HttpOnly and Secure session cookies. Review storage write
paths, logs, exports and injected implementations, not only helper functions.

Current inspected code: accounts/passwords.py defaults to scrypt N=32768,
r=8,p=1 with random16-byte salt and32-byte derived key; PBKDF2-HMAC-SHA256
600000-iteration fallback when scrypt unavailable. accounts/service.py hashes
signup/change/rehash values before storage and emits HttpOnly/Secure/SameSite
Strict cookies. preview_access.py sets Secure/HttpOnly Flask session flags.
These are offline code findings, not verification of production persistence or
hosted cookies. Store interfaces accept caller-supplied strings, so they alone
cannot guarantee every injected caller stores a valid hash. The closed synthetic
shared-service fixture uses labelled SHA256 test hashes, not password security,
and must never be wired for real users. Production login remains unwired.
