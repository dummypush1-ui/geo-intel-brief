# Mail mount implementation, not activation

Copyright (c) 2026 Push. All rights reserved.

Explicit MongoMailStore + blueprint + manual Apps Script bridge. Nothing is
imported by existing launchers. Runtime owner attaches the blueprint separately;
public107 read-only facade cannot be reused. No client, index, trigger or secret
is created here. No SMTP route or heavy dependency added.

Required source review: exact geo_intel articles/events/mail_control/mail_receipts
mapping, snapshot transactions, write permission, provisioned control schema,
canonical UTC datetime.isoformat article date fields. Mixed BSON/string dates are refused,
not silently treated as a complete weekly archive. No live source checked here.

Provisioning (runtime owner, not performed here): one mail_control row with _id
mail-v1, schema 1, revision 0, channel_id, policy, active {}. Channel is SHA256 of
UTF8 JSON with key order sender,recipients; sender is the lowercase Apps Script
effective-user email, recipients sorted lowercase unique addresses. Policy must
be supplied explicitly: fetched or displayed. No default. A config fingerprint
is a binding, not permission or authentication. Header secret is separate.

Snapshot query reads original top60 unsent articles then applies score4 display.
Weekly top20 plus DB category/country aggregates represent the entire queried
7day snapshot, not counters over only top20. Critical6h is bounded200 and uses
a separate mail_critical_sent flag (behavior change: suppresses repeat alerts).
Events are original digest-only90day entries, bounded200. All-low-score digest
skips unless critical/events exist, avoiding marking unseen articles in an empty
email. Stable ObjectId tie-break adds determinism absent from the old renderer.
Both behavior changes require approval before activation.

Receipt HTML and exact selected IDs are archived before send. Transactions
serialize all operations by replacing the control revision; no driver retries.
Claim gives a send permit once; another claim never gives permission to resend.
Acknowledgement atomically marks archived IDs, stores bridge acceptance and
clears active kind. Repeated ack is idempotent and never sends. Weekly never
marks; critical marks a separate flag. Arbitrary client article_ids are refused.

GmailApp return is only bridge_send_returned_not_delivery, not independent
provider verification or proof that the recipient got the email. Header holder
is a trusted bridge able to assert this receipt. It is not a public/untrusted
client endpoint. Secret rotation, sender/recipient authority and schedule are
runtime-owner decisions. No scheduling/triggers in this increment.

Apps Script persists nonce before prepare, claiming before claim, sending before
Gmail, and send_returned before ack. Lost claim response, send exception/crash or
failed persistence after send holds for manual reconciliation. No lease expiry
or automatic retry can resend an ambiguous send. Failed ack retries ack only.
Holding may miss mail; safety over silent duplication. Manual recovery is not
implemented. Parallel script copies are fenced by Mongo claim as well as local
script lock. An active kind prevents overlap even if a fresh nonce is submitted.

Archive retains full HTML without automatic deletion. Hard capacity128 fails
closed and requires reviewed export/retention work. This is not unlimited
weekly history, article backup, Telegram recovery proof or cleanup permission.
Mongo durable transactions need external review and real smoke test; local
mock tests do not prove an actual deployment. Bounded render may still fail on
schema drift, unsafe URLs, missing articles during ack or large events; failures
hold, never mark or send. Source URL constraints inherit save131 conservative
public-HTTPS/no-query validation. That restriction must be considered before
real mounting on existing article data.
