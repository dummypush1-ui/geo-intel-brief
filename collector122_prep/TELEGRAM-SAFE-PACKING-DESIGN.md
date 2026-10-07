# Next122 reversible backup packing and receipt state prep

Original formatter kept. Fix3500/codepoint/separator bug using actual UTF16 budget
including separators. Oversized full-record split into ordered continuation pieces,
never truncate full content. Keep URL/title/context manifest mapping each article
to ALL required piece indices, not a single pointer that loses continuation.
No real send. Returned text synthetic labelled NOT FOR DELIVERY.

Send state needs planned -> sending -> acknowledged/failed/unknown per message.
Durable receipt includes source article URL/content digest/batch-piece digest,
chat identity and provider message id. Unknown send latched, no retry until reviewed
provider reconciliation. Multiple refs per article changes original schema and
backward-compatible single head permalink requires explicit contract decision,
not assume one ref means complete. Partial backup visible; full content retained
in immutable bounded checkpoint until all required refs acknowledged. Don't drop
fulltext after keeping only300-char Mongo preview. Telegram limits current-source
verification and owner send/audience scope remain gates. No credential/client.

Reviewer122: SAFE as inactive synthetic structural scratch, not provider receipts,
authenticated durable state, or production proof. Renamed importable package for
staging, receipt uses relative packing import and inventory tests check inclusion.
Loaded state can be hand-edited to fabricate progress: validation is structural
only. Durable implementation must authenticate append-only transitions. Known
failure terminal is deliberate conservatism, not a reviewed retry policy. Provider
limits, rate controls, destination scope, multi-ref schema and runtime remain gates.
