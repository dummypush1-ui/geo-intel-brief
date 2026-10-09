# All-eight validator selection gate

The admission preflight now requires exact strict/error validators on all eight
fixed mappings. No mutation semantics change. New five validators come from:

| Mapping | Shape evidence | Validator scope |
| --- | --- | --- |
| collector_jobs197 | replay199_schema.source and durable_ledger._valid_document/_valid_job | fixed schema2 source, nullable active job, hot history64, closed counts, archive fields |
| finder_budget198 | replay199_schema.source, finder198_receipts._v2 and finder198_budget._state | fixed schema3 source, nullable active ticket, hot receipts64, archive fields |
| collector_replay199 | replay199_schema.manifest/record/validate_record and collector197_archive.pack | discriminated manifest/record; terminal collector rows, nullable retained checkpoint1/2 |
| finder_replay199 | replay199_schema.manifest/record/validate_record | discriminated manifest/record; complete broker receipt, null fingerprint/checkpoint |
| collector_checkpoints197 | DurableCheckpoints.put/get and CoverageCheckpoints.put/get, native201_coverage.checkpoint_row | closed checkpoint1/2 envelopes with bounded encoded arrays and exact hash/fence/version fields |

No fallback collection. Encoded content is genuinely variable recursively, but
its top-level projection is fixed. DB schema checks its bounded array envelope;
existing _encoded_budget/_decode/capture, hash and cross-field/source-chain checks
remain mandatory. Validators are structural envelopes, not substitutes for
hashes, key/fence uniqueness, phase relationships, budgets or archive-chain proof.
All three existing journal validators remain byte-equivalent in value.

## Explicit correction to prior native docs

Prior NATIVE200BA/BC/201A references to a restricted no-creation role are
SUPERSEDED. MongoDB INSERT permission itself permits creation of a non-capped
collection. Removing CREATE_COLLECTION does NOT make an insert-enabled role
creation-proof. The revised gate2 requires least-privilege find/insert/update on
exact mappings, listCollections/listIndexes for inspection, no extra/inherited
roles or explicit DDL grants, plus an owner-only exclusive DDL boundary while
the native path is enabled. No concurrent drops/schema changes are allowed.

The inspection-to-insert TOCTOU window remains accepted. An administrative drop
inside it can allow ONE write into a recreated unvalidated collection. The next
inspection rejects its missing exact validator, holding the source. This is
fail-closed continuation, NOT a zero-effect race guarantee. Tiny timing is only
mitigation. No claim of transaction durability or live enforcement is made.

All-eight bare recreation rejection is tested before the next write. Actual
Mongo $or/oneOf validation, listCollections normalization, BSON numeric types,
in-transaction maxTimeMS and DDL/recreation behavior must be verified on separately
authorized staging. No schema installation/Atlas operation is included.

Source-only/defaultOFF/unselected. Old199/200a/200b-a preflight and every native
journal/core/adapter unchanged. Admission preflight strictening is deliberate,
so the previous journal-only schema installation now refuses to enable. Gate2
owner package must install/verify the new full schema set before selection.

Official grounding:
https://www.mongodb.com/docs/manual/reference/command/create/
https://www.mongodb.com/docs/manual/reference/method/db.createcollection/
https://www.mongodb.com/docs/manual/reference/command/insert/
https://www.mongodb.com/docs/atlas/security-add-mongodb-roles/
https://www.mongodb.com/docs/atlas/reference/custom-role-actions/
