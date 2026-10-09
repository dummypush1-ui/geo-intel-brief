# Gate2 owner steps package: review first, no activation

The offline owner_package(fingerprint=..., clock=...) function returns request
DATA only. It opens no client, reads no URI/environment, executes no command and
writes no file. Use the exact reviewed repo snapshot and pinned4.18.2 environment.
Fingerprint must come from the reviewed collector catalog/config, not a made-up
value; clock is the owner-reviewed initial integer source clock in UNIX epoch
seconds, NOT milliseconds. ready stays false.
The package is not proof that an Atlas cluster or account is configured correctly.

## 1. Choose and inventory before any mutation

Owner confirms the intended Atlas project/cluster/account, geo_intel DB, replica-
set (not sharded/mongos/loadbalanced), current server version and maintenance
window. Preserve an owner-controlled complete snapshot/backup and document the
restore path before changing schemas. Keep the proposed native selection and any
new collectors OFF. This package does not stop any existing collector or writer.
Before any schema installation, identify EVERY process writing EACH of the eight
collections, including pre-existing 197/198 collectors, broker writers, jobs and
manual/admin tools. Record the owner-reviewed writer inventory per collection.
Proceed only if a collection is verified new/unused, or ALL its current rows AND
EVERY current writer already satisfy its exact proposed validator for every
write shape. strict/error can reject legacy writes, even when current rows pass.
If writer identity, compatibility or quiescence is unknown or incompatible, STOP.
Any stopping, migration or writer change needs a separately approved preservation
plan; this package grants none and must not disrupt a running legacy writer.
Inventory all8 collections, current validators/indexes and exact source/guard/
genesis documents. No secrets in screenshots, logs or package evidence.

Use the package's readonly_verification_commands on the selected DB, one by one.
They inspect exact names, collection options and exhausted index cursors, not
user authorization. All8 must be ordinary pre-existing collections, unique
ordinary _id, no TTL, no view/time-series mapping. Validate source and complete
archive chains with the separately reviewed read-only200c-b harness when ready.

STOP if collection identity, state, existing data, backup, fingerprint, topology
or permissions are unknown. Do not infer empty from an empty cache or a failed
query. Retained checkpoints may be v1 orv2; all hot/archive/journal data must remain.

## 2. Separate administrator and runtime identities

Configure Atlas custom roles through Atlas UI/CLI/API, not db.createRole in
mongosh: Atlas manages those roles and can roll back out-of-band role changes.
The package role JSON is a request payload, not a command sent by this code.
Assign the operational identity ONLY the reviewed custom role: exact8 FIND,
INSERT, UPDATE, LIST_INDEXES, plus DB LIST_COLLECTIONS. Inspect all additional
built-in/custom/inherited/specific user privileges; Atlas privileges combine.
No REMOVE/drop/collMod/createIndexes/createCollection/validation bypass/admin
or broad readWrite role is proposed. Use a separate owner admin for schema DDL.
The coarse role may later be narrowed per collection if separately reviewed.

IMPORTANT: this is least-privilege, NOT creation-proof. MongoDB permits non-capped
collection creation with INSERT on that collection, even without CREATE_COLLECTION.
Mongo privileges are grants, not a deny list that overrides other roles.

Owner-only exclusive DDL is an operational requirement while native selected:
no concurrent collection drops, schema/index changes or restoration. The
inspection-to-insert race can permit ONE write into a recreated bare collection.
The NEXT exact-schema inspection holds. This accepted limitation is not zero-
effect safety. Role restrictions alone do not eliminate it.

## 3. Install exact schema requests under explicit owner approval

schema_requests contains both create_if_verified_absent and
modify_if_existing_owner_reviewed. These are alternatives, never run both.
- Verified absent: owner admin may create the exact collection with its reviewed
  validator, strict validationLevel and error validationAction.
- Existing: owner reviews ALL current rows against the new schema before choosing
  collMod. strict does not retroactively prove old rows valid.
- Unknown/mismatching shape: STOP. Do not delete, replace, relax or coerce records
  merely to make validation pass. No generic migration tool is included.

### Preserve integer types before any approved command

The returned Python objects are request data, NOT copy-paste execution commands.
Each concrete command, chosen identity, target and final typed payload requires
owner review and approval. Do not paste ordinary JSON into a JavaScript shell or
Atlas editor. Large bounds include 9223372036854775807 (int64 max); a JS Number
cannot preserve it exactly. Even exactly representable numeric values must not
be stored as doubles where the reviewed schema/data expects int/long.

Use Canonical Extended JSON v2 for transport, generated offline from the reviewed
package through pinned PyMongo 4.18.2. This serialization fragment performs no DB
operation and assumes `package` is the reviewed owner_package return value:

```python
from bson.json_util import dumps, loads, CANONICAL_JSON_OPTIONS
requests_ejson = dumps(package['schema_requests'],
                      json_options=CANONICAL_JSON_OPTIONS, sort_keys=True)
genesis_ejson = dumps(package['empty_new_genesis_templates'],
                     json_options=CANONICAL_JSON_OPTIONS, sort_keys=True)
# Decode only through the pinned driver's Extended JSON decoder, not json.loads.
typed_requests = loads(requests_ejson, json_options=CANONICAL_JSON_OPTIONS)
typed_genesis = loads(genesis_ejson, json_options=CANONICAL_JSON_OPTIONS)
```

Canonically encoded signed int32 values use {"$numberInt":"5000"}; int64 bounds
and integer clocks outside signed int32 use {"$numberLong":"9223372036854775807"}
(or the exact clock's decimal string). Booleans stay booleans, not integers.
These wrappers are transport representations: decode them into BSON numeric
values before any separately approved DB command. Never install the wrappers
as literal validator subdocuments, run JSON.parse on them as a substitute for an
Extended JSON decoder, use relaxed serialization, or convert values through float.
If a chosen UI/tool cannot prove lossless typed decoding, STOP and choose a
separately reviewed typed command path. Large epoch-second clocks still use
int64; the input unit remains seconds. This is not a BSON Date/millisecond value.
Genesis ordering and idempotency remain deferred to a future approved harness.

The exact admission validator set includes five source/archive/checkpoint schemas
plus3journal schemas, with an $or outcome/admission validator. Hashes, complete
chain, fence uniqueness, phase relationships and recursive typed checkpoint
content still require app validation. DB structural schemas do not replace it.

After each separately approved install and before further setup/selection, run
the corresponding read-only verification commands through pinned PyMongo 4.18.2
on the verified geo_intel DB. Require the exact intended collection, exhausted
cursor and strict/error options; compare its returned validator against the
reviewed VALIDATORS entry. In addition to the admission preflight's object-value
comparison, require type-preserving canonical equality using the same pinned
`dumps(..., json_options=CANONICAL_JSON_OPTIONS, sort_keys=True)` on each side.
This stronger owner check distinguishes an int/long from an equal-valued double
(Python numeric equality alone does not). Any int-vs-double difference, lost
precision, int-width drift or missing/unverifiable readback means STOP, retain
the evidence and get source review. No automatic repair/coercion is authorized.
Use the same typed exact readback for any later approved genesis insertion.
Compare actual listCollections validator objects to the package EXACTLY as the
admission preflight does. Do not treat equivalent-looking normalization as PASS:
if the server returns a different $or/oneOf/schema form, STOP for source review.
Real server normalization and BSON numeric types remain unmeasured. No index
creation/drop request is emitted; resolve non-ordinary _id or TTL with a separately
approved preservation plan, not a blind dropIndexes command.

## 4. Genesis templates apply ONLY to a verified brand-new empty install

empty_new_genesis_templates contains collector/broker source, batch0 manifest and
idle serial0 guard per family. These are templates, NOT writes. Insert only after
owner confirms all dependent mappings are empty and each ID absent, and approves
the final documents, snapshot and actual collector fingerprint. Use majority+j
and exact readback if the owner later authorizes the setup. No upsert or overwrite.

Existing v1/v2 ledgers/budgets, any calls/fences/active jobs/receipts/history,
checkpoints, archive chain or journal entries invalidate new-empty templates.
STOP and commission a separate migration plan preserving every full record and
hold. Never reset calls, fences, serials or active tickets; never truncate hot64.
No converter or replay/recovery permissions are supplied.

## 5. Verify on actual separately authorized staging

Before gate2 can pass, record actual server/version/topology and role evidence,
all8exact returned schemas/indexes, valid full sources/chains, and hashes of the
reviewed request package. Read-only200c-b checks may establish observed state,
not crash durability or live-readiness. Required staging checks still unrun:
- Actual $or/oneOf/$jsonSchema acceptance/rejection for all lifecycle shapes,
  checkpoint1/2, BSON int/long bounds, schema normalization and strict/error.
- Pinned no-retry native transaction/body maxTimeMS behavior on that server.
- Owner-approved disposable drop/bare-recreation test, verifying NEXT write
  inspection refuses; preserve accepted one-write race in the report.
- Actual known/unknown commit/abort/crash persistence and3GiB workload proof.

The last items are mutating measurements: require a future separately reviewed
write harness with owner-approved disposable mappings/effects. The current fixed
geo_intel client/store cannot be repointed to an invented staging DB. Do NOT run
these tests on production or infer proof from the loopback fixture. No dormant
write tests are included in the read-only harness.

## 6. Completion is not cutover

Gate2 observed PASS alone does not turn collectors on. Owner diagnosticgate3,
reviewed production factorygate4 and explicit final ownerOKlive gate5 remain.
201c is held until gate2/3 contracts align. Old collectors are not stopped, emails
are not sent, and deployment/live switches are not touched by this package.
Do not confuse "new native selection OFF" with permission to stop existing
writers. The section 1 per-collection writer-compatibility STOP applies before
any strict validator change, independent of all later cutover gates.
DB-level LIST_COLLECTIONS exposes all collection names in geo_intel; this is
an accepted scope of the proposed role, not a collection-name privacy boundary.

## Official sources fetched for this package

- Create privileges, INSERT permits creation:
  https://www.mongodb.com/docs/manual/reference/command/create/
- Implicit creation, including transactions:
  https://www.mongodb.com/docs/manual/reference/command/insert/
- Atlas role management and combined grants:
  https://www.mongodb.com/docs/atlas/security-add-mongodb-roles/
- Atlas action names:
  https://www.mongodb.com/docs/atlas/reference/custom-role-actions/
- Collection options and verification command:
  https://www.mongodb.com/docs/manual/reference/command/listCollections/
- JSON schema and query-operator validation:
  https://www.mongodb.com/docs/manual/core/schema-validation/specify-json-schema
- Transaction runtime/DDL limitations:
  https://www.mongodb.com/docs/manual/core/transactions-production-consideration/

- Canonical Extended JSON and pinned Python serialization/decoding guidance:
  https://www.mongodb.com/docs/languages/python/pymongo-driver/current/data-formats/extended-json/
- Numeric Canonical Extended JSON v2 representations:
  https://www.mongodb.com/docs/manual/reference/mongodb-extended-json/
