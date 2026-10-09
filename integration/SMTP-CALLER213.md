# 213: unselected 204 -> 174 closure-construction caller

This is source-only preparation, not SMTP activation, mail wiring completion or
item24 closure. Apps Script stays selected; SMTP fallback stays held. Existing
174/204 modules, original legacy BRICS direct sender and mailv1/212/201 production
composition are unchanged. No route, environment, client, timer, retry, ledger,
receipt, marking, resolution, scheduling or send identity is added or chosen.

build_sender(enabled=False, **arguments) returns (None, static metadata):
selected=False, prepared_not_sent=False, state=disabled,
selected_rail=apps_script, smtp_fallback_held=True. OFF touches no settings,
credential/address/capability argument and imports neither174 nor204; extra or
missing arguments are irrelevant OFF. enabled must be an exact bool.

Enabled construction requires exactly settings/user/password/mail_from/mail_to.
settings is an exact built-in dict with exact built-in str keys and scalar
str/int values;204 owns its closed keys and profile/port/host/mode/timeout rules.
Subclass dict/list/str/scalars are refused, not passed to permissive174 checks.
Missing/extra arguments and unknown204keys refuse with fixed text. No defaults
come from environment. The adapter passes an independent settings dict and copy
of the recipient list through actual204binding_data -> actual174smtp_sender.
Geo default465/implicit_tls; BRICS default587/requiredSTARTTLS. Explicit reviewed
465/implicit_tls or587/starttls pairs accepted for either profile; mismatched
pairs refuse before closure creation. No arbitrary sender factory is accepted.

username is exact str,1..320 characters, ASCII0x21..0x7E (no spaces). Password is
exact str,1..1024 characters, ASCII0x20..0x7E (spaces preserved literally).
Non-ASCII passwords are REFUSED, never altered. This prevents smtplib.login's
ASCII encoding error from exposing a secret character/position inside send.
No normalization/stripping of credentials occurs. No credential is logged,
printed, returned in metadata, repr, exception or exception chain.

mail_from is exactASCIIstr <=254 matching the legacy address grammar with
FULLMATCH. mail_to is an exactlist of1..20 exactstr addresses with the same
fullmatch/cap; comma-joined strings/tuples refuse. Trailing newline, leading
space, embeddedTAB, Unicode and case-insensitive duplicates refuse. This is a
closed legacy grammar, not universal RFC mailbox support or proof of ownership.
Subject/body are not prevalidated/authored by213, they stay174-owned on future
call. A caller still needs approved sender/recipient/final words together.

Enabled build returns (wrapped174send_callable, static metadata):
selected=False, prepared_not_sent=True, state=prepared_capability_not_selected,
selected_rail=apps_script, smtp_fallback_held=True. The CALLABLE IS A REAL SEND
CAPABILITY once built, even though metadata says not selected. Building it makes
no socket, DNS, TLS context or send. A future selected/authorized caller could
invoke it, so OFF/source-only labels are not a capability-security barrier.
No current production/mailv1/201/ledger module imports smtp_caller213; AST import
edge tests verify this. Import itself has no network/env/context/effect.

All204/174construction and future174send exceptions are replaced by fixed
CallerRefused('SMTP caller refused') raised fromNone OUTSIDE except blocks, so
__cause__ and __context__ carry no upstream credential/settings fragments.
This intentionally replaces174DeliveryError with the caller's fixed refusal;
it is NOT a safe resend signal. Success returns the original174result (None).
Neither None nor refusal is used to acknowledge any receipt in this unit.

## Transport uncertainty, unchanged174

174 uses ssl.create_default_context with certificate/hostname verification.
465 usesSMTP_SSL;587 usesSMTP thenEHLO/STARTTLS/EHLO/login/sendmail. Missing or
refusedSTARTTLS fails BEFORE credentials and send, never plaintext fallback.
Construction verifies config only, not DNS/private-host safety, realserver
compatibility, credentials, quota or actual intended recipient. Those are
future activation decisions;213does not turn an injected hostname into authority.

174 discards sendmail's per-recipient refusal dictionary. When SOME recipients
are refused, sendmail may return that dictionary rather than raising. Therefore
174's None return does NOT prove all-recipient acceptance or delivery. When ALL
are refused SMTPRecipientsRefused normally raises. Connection context exit sends
QUIT; a QUIT error AFTER send acceptance may raise SMTPException and174maps it
toDeliveryError. Thus DeliveryError/213CallerRefused also does NOT prove unsent.
Future212-ledger caller MUST treat every error-after-start as POSSIBLY SENT,
leave started held, and never infer operator_resolved_unsent from DeliveryError.
No retry/fallback/ack/mark is added and174is deliberately unchanged. No email-sent
or independently verified delivery claim is made here.

## Grounding and tests

Actual live current integration/geonews_digest/delivery.py matched landedsource
SHA256527be6ca3a1a42d3e384195f57cfd899940f84f0f72fc25c3a1f7ea9a46985e1.
OriginalGeo reports/email_report.py SHA25630d7552def0e9d56f8981f25b3d81ed3475bcc354971aea304a30e6f7d583688
andBRICS- reports/email_report.py6582d81d184e2c18842f1507d7e46042514c9d0cfbfea7e1202ce8bf1218ac65
were read live during212grounding: GeoSSL465 vsBRICSSTARTTLS587, notexecuted.
CPython3.10.12 smtplib login/sendmail/context-exit semantics motivate ASCII
credentials and uncertainty caveats; source inspected, no realSMTPcalled.

11newoffline tests plus204/174 (25total): real204->174profiledefaults andexplicit
pairs with mockedSMTP, exacthost/port/timeout/contexttype andverifiedTLS/order,
STARTTLSnot-supported/error beforelogin, mismatchbeforefactory, credentialcaps/
ASCII/nonASCIIcanary never174, addressfullmatch/newline/TAB/duplicates/21/255cap,
exactsubtypes/keys, exceptionchain/refusal/repr, OFFhostileargs/importtrap,
moduleimport/buildsocketDNScontexttraps/noenvread, copyindependence, partial
recipient refusalNone andQUITerrorafteracceptance, ASTnocurrentimportedge.
MockSMTPcalls are tests, not realnetwork/email effects. No current sender is
wired. Remaining: realcaller/212receipt/authscope/legacyBRICSexclusion/205schedule/
AppsScriptbridge/DBhistory+activation. SMTPfallbackremainsheld,201cstillheld.
