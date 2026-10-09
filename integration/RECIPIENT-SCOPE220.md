# 220: supplied recipient config fingerprint

DefaultOFF static flags; explicitTrue validates supplied config only. No address
is searched, selected, inferred, autofilled, contacted or retained. Owner has not
provided or approved a recipient list. send_allowed/ready/owner_approvalFalse.

Exactlist1..20 exactASCIIstr addresses<=254,213legacyfullmatchregex. May refuse
validRFCaddresses; refusal is not a claim an address is invalid. Acceptance is not
proof of validity or deliverability (legacy regex accepts a@b..com). No trim, display
name/comment/quotedlocalpart/comma-string/Unicode/space/control support. Duplicate
case-insensitive addresses REFUSE, never silently dedupe. Input remains unchanged.

Protocol lowercases WHOLE addresses including local part, then sorts. Real
mailboxes may treat localpart as case-sensitive; owner must accept this policy
before first use. Case variants share fingerprint; permutation doesn't matter.
No aliases/Gmaildots/plustags/DNS/ownership or mailbox-equivalence rule is inferred.

Hash is canonical sorted-key/separator/ASCII JSON SHA256 of closed
{schema:email_recipient_set220_v1,kind:email,recipients:sortedloweraddresses}.
This length-safe schema value supplies domain separation, no joined delimiter.
Plain64hex is accepted by219/212 tests only. Output contains fingerprint/policy/
count/flags only, no actual address/name/sender/bridgechannel. Errors fixed with no
address/cause/context. Hash is NOTprivacy/anonymity; guesslists can test addresses.
Do not log fingerprints together with addresses.

Not bridge identity: bridge hashes sender+recipients,220onlyrecipients.220 does
not compute/return bridge MAIL_V1_CHANNEL. Sender change is invisible to220and
212logicalchannel unless a later unit binds sender: NAMED BLOCKER for ledger wiring.
Recipient change makes a new fingerprint/channel; exclusions/history do not carry
over automatically. Owner must decide changes and approve actual recipients/words.

No219212constructor/ledger/store/SMTP/bridge/production import or config/property
write. No DBURL/read/check/write/creation/files/network/send/activation/cutover.
Existingbridge216/217heldsurface/219bytes unchanged. AppsScriptselected/
SMTPfallbackheld/201cwriteheld. History/exclusion/marking/reconciliation/mount,
durablebody/recipientpolicy/words/liveworkflow remainopen. This is data only.
