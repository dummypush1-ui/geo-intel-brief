# 215: optional existing-schema review data

The owner asked for DB wiring without a collection check, not schema changes.
This optional data is neither a pending step nor a gate for wiring. Nothing will
run it. Do not present it as an action to approve unless a later scoped unit
actually needs schema changes. Calling optional_schema_review authorizes nothing.

The function does not inspect collections, construct a client, read a DB URL,
read environment or files, install schemas, create collections, seed genesis,
change roles or counters, select runtime behavior, or execute DB commands.
It proves nothing about collection existence. Existing state and history remain
unverified. No automatic follow-up occurs when a DB URL appears.

validation_level is required. The reviewer explicitly chooses strict or moderate;
there is no default. Strict validates all later inserts and updates, including
updates of existing invalid documents. Moderate validates inserts and updates of
existing valid documents but skips validation of updates of existing invalid
documents. This choice changes whether existing rows can be updated. Neither
choice proves existing rows or writers compatible. Proposed validation action is
error. These are optional review values, not permission to tighten a live schema.

The eight names are the current fixed native names, sorted. Validators are
independent deep copies of the actual current VALIDATORS constants captured at
module import, not schema observations. Tests pin canonical validator hashes so
future source drift needs a fresh review. articles/events are not included.

request_data_not_executable contains descriptive fields, not collMod/create
command wrappers. No element is directly usable as a pymongo db.command request.
A future separately approved executor would need deliberate translation and a
copy step. This unit supplies no executor or execution instructions. Proposed
majority/j=True/wtimeout=5000 is data only, untested against a real server.

No create or missing-case branch, genesis template, read command, source clock,
fingerprint, reset, role request, upsert, repair, or callable is returned.
If separately authorized future work discovers missing collections, it must hold;
creation requires a separate explicit owner decision. This unit never discovers
missing collections and never initiates that future work.

Existing writers and rows might be incompatible with a proposed validator.
No backup/custom-role ask is reopened here; closed asks do not prove those gates
satisfied. Preserve articles/events and all existing native state. Any future
schema change needs exact scope and owner permission, not this review data.

AdmissionStore INSERT/drop TOCTOU remains open: inspection can precede an admin
drop and one insert can recreate a collection. This unit proves nothing about
no automatic creation. 201c write selection stays held; prior ONE-write wording
is not permission for that effect under the owner's no-auto-creation boundary.
No live DB read/write, presence check, provisioning, activation or cutover occurs.

Validation-level semantics source:
https://www.mongodb.com/docs/manual/core/schema-validation/specify-validation-level/

Transitive imports: this module's own imports are stdlib copy and static
constants, but native200_admission_preflight loads pymongo,
native200_transactions, native200_store, native200_admission_store and
native201_schemas. Importing 215 requires the pinned pymongo environment;
215 is not "no pymongo/no store import" at runtime. Those imports do not connect
or read a DB. Nothing in production imports 215.
