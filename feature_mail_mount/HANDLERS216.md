# 216: OFF-by-default manual Apps Script dispatch

mailV1Digest216, mailV1Critical216 and mailV1Weekly216 map respectively to
runMailV1('digest'), runMailV1('critical') and runMailV1('weekly'). Each passes
one literal argument only. These names do not replace the declared HANDLERS
mailV1Digest/mailV1Critical/mailV1Weekly; those remain without wrappers.
The existing companion, bridge, HANDLERS table and routes are unchanged.

Editor Run passes no arguments, so it always returns OFF. A trigger event object
is refused. Exact primitive true is reachable only from another function or a
scripts.run API caller. Do NOT deploy this project as an API executable with
these functions. The file contains no true caller, installer or automatic call.
Wrappers must not be called in any real run under this source-only unit.

False/undefined returns a frozen off/no_send_attempt object before any bridge or
Apps Script service lookup. Extra arguments are ignored without access. Other
values refuse with fixed mail216_refused. ON calls the existing bridge, which
still separately requires MAIL_V1_ENABLED exactly 'true'. 216 reads/writes no
properties, creates no triggers, deploys nothing and changes no collector path.

Wrapper ON IS A REAL SEND CAPABILITY through the existing GmailApp bridge.
Source/default-OFF is not a permission barrier. No real send until the owner's
final recipient and words are confirmed and all other mail gates are satisfied.
All tests use spies or mocked Gmail, never real Gmail or Google services.

Only off/skipped/acknowledged are accepted bridge states. Output is frozen static
state/scope data; no recipient, subject, receipt ID, count or arbitrary text is
passed through. Malformed/unknown return uses fixed mail216_unknown; errors from
the bridge use fixed mail216_possibly_sent, even if a failure occurred before a
send. No raw message/stack/name or Logger output is retained. Neither error nor
acknowledged proves delivery or non-delivery. Off/skipped means this invocation
made no send attempt, not proof about older pending attempts or delivery.

claimLost, Gmail failure and persistAfterSend hold the existing pending phase;
216 never clears it, invents a nonce, retries a send or falls back to SMTP.
An ack-only bridge retry remains ack-only. 216 does not implement reconciliation.

Current mailv1 has old 128-cap receipts and does not enforce 212 exclusion keys.
History, marking, sender/recipient scope, DB timing, weekly identity, mounting and
reconciliation remain open. Mailer activation is separate from collector cutover.
Apps Script stays the selected rail; SMTP fallback stays held. No trigger rebuild,
activation, live sends, live DB access or collector cutover occurs here.

mail216_unknown after a bridge call must be treated like possibly_sent, never
"not sent"; do not retry on unknown.
