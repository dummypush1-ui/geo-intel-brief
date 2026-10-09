# 223: supplied exclusion view consistency only

This projection is a caller assertion, not a ledger read. Two caller-supplied
acknowledged-ID lists agree. That does not prove either list is a ledger view.
The closed, non-native projection has these fields:
- schema: mail_exclusion_projection223_v1
- logical_channel: lowercase 64-hex string
- purpose: digest
- acknowledged_ids: exact tuple of unique ObjectIds, at most 10000
- active_state: None, prepared or started

None means "caller asserts none", not evidence of no active control. Prepared
or started refuses the whole asserted channel and purpose, even with no article
overlap. Unknown, cancelled, resolved and all other states refuse. They are
never treated as None. 223 mirrors only active prepared/started on this channel
and purpose. 212 itself owns its control rules.

The email tuple must have exact set equality to the projection IDs. There is no
deduplication. Order does not matter. All three exact email/telegram/whatsapp
tuples are checked for type, uniqueness and caps before copying or set conversion.
Other channels are not unioned or compared. A telegram-only article inside the
window is not excluded and is not an error. 221 receives displayed_receipts
unchanged; a deep comparison checks that after the call.

221 checks independent expected fingerprint and nonce, then fully re-freezes
219. Channel equality is checked after that verification; purpose is exactly
digest. The 219 candidate union strings must be disjoint from the projection
ObjectId strings. Renderer 218 already excludes email receipts. An overlap means
candidate and supplied view disagree, so the check refuses.

Omission in BOTH views passes. Stale views pass. Both views can be forged or
incomplete. This is no delivery, receipt membership, current active state,
history completeness or no-repeat proof. No authenticated native projection
producer from 212 exists. That producer, with an authenticated read under future
permissions, remains an open item. No read is performed here. None does not
permit a live workflow. Supplied rows matching 221 is not provenance or freshness.

Default OFF before arguments or imports. ON dynamically imports 221, 219 and
bson; 218 is reached through 221. There is no 212 import or constructor, driver
check, live DB client, query, write, creation, index change or store. The fixed
refusal is raised outside except without upstream message, cause or context.
The closed constant result contains a note and flags, not IDs, counts, channel,
projection or receipt_status. send_allowed, ready, owner_approval,
receipt_membership_verified, history_complete, source_complete, durable and
ledger_wired remain False. No output receipt conversion or input mutation.

No send, wiring, property or environment change, deployment, activation, trigger,
cutover, mount or selection. Apps Script remains selected, SMTP fallback held,
217 held and 201c write held. The sender blocker from 222 is prepared, not
resolved. History, exclusion authority, provenance, durable body and approval
of recipients and words remain open. The owner has not approved recipients or
words. Native 212 article prepared/started keys and its active pointer are not
validated or mapped by this unit.
