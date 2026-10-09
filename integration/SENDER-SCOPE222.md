# 222: supplied sender-inclusive scope DATA only

NAMED sender-binding BLOCKER is prepared, NOT resolved. No consumer checks this
value against the real sender.212/219/bridge do not consume222; sender change is
STILL invisible to212logicalchannel. ledger_wired/bridge_wiredFalse. No sender or
recipient list provided or approved by owner. No default sender/autofill/Session
or effective-user lookup. Bridge sender is ONLY Session.getEffectiveUser().getEmail()
.trim().toLowerCase();222neverclaims supplied sender matches that real identity.

DefaultOFF before argument/import access. ON accepts one exactASCIIstr sender<=254
with213legacyfullmatchgrammar, and calls real220for suppliedrecipientlist. No
recipient grammar copied here. Refusal may reject validRFCaddresses; acceptance
isn't validity/deliverability (legacy regex accepts a@b..com). No trim/aliases/DNS.
Sender equal to a recipient is allowed; separate fields, no cross-field dedupe.

220/222refuse whitespace. Realbridge trims sender and each comma-split recipient;
'a@example.invalid, B@example.invalid' works inbridge, raw secondaddresswithspace
refuses220/222.222inputs must already be normalized addresses; future wiring must
apply the same trim rule before calling220, with owner-reviewed address selection.
Wholeaddresslowercase includinglocalpart is an explicitpolicyowneracceptancebefore
use; realmailboxes may treatlocalpartcaseassensitive. Sortedrecipientpolicy220.

Sender fingerprint: canonical sorted-key/no-spaces/ASCII JSON sha256 of closed
{schema:email_sender_fingerprint222_v1,domain:email.sender222,sender_lower:loweraddress}.
Scope fingerprint: samecanonicalsha256 of closed
{schema:email_sender_recipient_scope222_v1,sender_fingerprint,recipient_set_fingerprint}.
220recipientfingerprint unchanged. Newhashes NOTlegacybridgeMAIL_V1_CHANNEL, no
replacement for212logicalchannel/219binding. Realbridgelegacyhash is JSON.stringify
{sender,recipients} in THAT insertion order (senderfirst), lower/sort/trim; no sorted
keys. Test executes realbridge in NodeVM ONLYuntil digest, no lock/send/request.
Module never computes/returnsbridgevalue. Sender changesnewscopehash, not220fp.

Closed output3hashes/policy/note/Falseflags only, no addresses/count/name/rawlists.
Hashes NOTprivacy/anonymity: candidate addresslists can guesssenderhash and test
recipientsets. Don't logfingerprintswithaddresses. Fixedrefusal no upstreammessage,
cause/context. No words/nonce/content binding, authority/provenance/effectiveidentity.
History inheritance and exclusions on sender orrecipientchange needseparateowner
decision; no automaticnewchannel/historymigration/inheritedexclusions.

No DB/check/read/create/store/send/ledger/productionedge/property/env/deployment,
activation/triggers/cutover/mount/selection. AppsScriptselected/SMTPfallbackheld,
217held/201cwriteheld. Laterledgerunitmustconsumevalue andcheckagainstrealselected
rail/effectivesenderandstoredbinding. Otherhistory/exclusionauthority/provenance/
durablebody/recipientswordsapprovalopen. Config DATA only, allflagsFalse.
