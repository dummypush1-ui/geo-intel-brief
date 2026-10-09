# 219: in-memory candidate bytes, not archived

freeze_candidate defaultsOFF before inspecting arguments or importing any other
integration. ON takes a supplied nonempty218-shaped result, a caller-supplied
lowercase64hex SHA256 recipient-set fingerprint and a20..80ASCII nonce of letters,
digits,underscore,hyphen. It validates closed shapes and internal consistency,
then returns (immutable bytes, independent plain binding dict). Bytes are not
written anywhere. archived/durable/send_allowed/ready stayFalse.

Recipient fingerprint will come from a future recipient unit.219 cannot verify
it refers to real addresses or owner-approved recipients. No address/name is
included in binding. Proposed fields are212input data, not permits or proof.
No call to212/218/217/216/store/DB/file/network/env/sender occurs. No production
module imports219. OFF imports no pymongo or dependent integration.

CanonicalASCII JSON bytes contain candidate and proposed_content_digest. Exact
bytes type is required; bytearray/memoryview/subclasses refuse.128KiB cap includes
the envelope. Candidate combinedbody80KiB/html60KiB and IDunion120 still apply.
verify_snapshot parses strictUTF8/noBOM/duplicates/nonfinite then requires EXACT
canonical re-serialization bytes. Whitespace, key order,escape variants,newline,
secondvalue and mutations refuse. Every candidate/binding field is checked,
contentdigest recomputed, wholebinding recomputed,then independentcopyreturned.

218digest keeps its exact canonical candidateJSON formula.212compatible channel,
control,binding andnonce hashes keep exact formulas WITHOUTnewdomains. Separation
is only by their different closed JSON key sets and212purpose field; no claim of
cryptographic non-collision is made. Only new219snapshot_identity andbyte_integrity
use separate versionedASCII domains over canonical length-safeJSON. Tests pin
hardcoded212/218vectors and compare against actual212purehelpers in tests only.

Internal consistency is NOT authentication. A changed HTML candidate with a
recomputed digest/binding is accepted; tests show this deliberate limitation.
219 does not sanitize HTML or establish that218 produced it. A future unit
holding original rows must re-derive218 output when provenance matters. Hashes
bind this candidate, not source completeness, owner wording/recipient approval,
safe rendering or persistent retention. Neither canonical bytes nor nonce grants
send/retry/newnonce/clear/ack/mark authority. Empty218skiprefuses without binding.

218desktop/mobileChrome pixels remain the only visual evidence.219changes no
visual surface and makes no Gmail/Outlook claim. Real immutable durable storage,
existing-state preservation/history/import, exclusion enforcement, marking,
recipient/words authority,reconciliation,mapping,realmount andsendworkflow remain
open.217held/216unselected/AppsScriptselected/SMTPfallbackheld/201cwriteheld.
No DB check/read/write, automatic creation, live wiring/send or cutover occurs.

Bytes commit only to candidate/content digest, not recipient fingerprint or nonce;
only binding commits to those. The same bytes can verify with a freshly frozen
binding for that candidate and another fingerprint/nonce. verify_snapshot proves
bytes and binding agree, NOT that these bytes were used for a given send. Future
ledger wiring must retain binding hash together with content digest and re-derive
218 from original rows before sending. Nothing is persisted; restart loses the
bytes. Durable body storage remains open.212_hash defaults ensure_ascii=False;
219usesTrue. Compatibility equality here relies on ALL formula values beingASCII,
including IDs/hashes/fingerprint/nonce; test matrix is deliberately ASCII-only.
