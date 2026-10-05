# One-database mapping preparation

Historical/direct-adapter scope: this describes SingleDatabasePlan and the
separate two-project compose_single_database seam, not the later Geo-only
private_router. Current selected Geo-only read factory and separate events
composition are described in FEATURE_STATUS.md and GEO_EVENTS_COMPOSITION_LIMITS.md.
This seam remains unwired; do not read its old wiring limits as global status.

SingleDatabasePlan is an offline caller-supplied label/map fixture. It does not
connect to MongoDB or change runtime.compose. The selected existing Geo database
will be the eventual destination, but its actual database/collection names,
ownership, schema and indexes must be verified before configuring real reads
or writes. No label is inferred from legacy defaults.

Two distinct project article maps model two separate collections in one DB.
This preserves exact-URL versus hash identity semantics. Old separate DB and
its records remain untouched. No migration, index creation, dedupe update or
alert delivery occurs. Live writer and cutover remain separate approvals.

Runtime currently supports the preserved two-project read configuration. This
new fixture does not replace it or declare it safe to point both projects at
one articles collection. Single-DB runtime wiring remains unfinished.

single_db_runtime.compose_single_database is now a separate, unwired preview
composition seam. It takes one explicit injected client factory, one URI and a
reviewed plan, retaining separate project collections and private access gates.
There is no default MongoClient or private_router wiring. It can perform reads
if deliberately wired and enabled later; current tests inject fake clients.
No claim is made that arbitrary caller factories are effect-free. The factory
is trusted composition code, not untrusted config/data. Mapping failures close
the created client. No writes/index creation/migration/delivery are added.

Factory failures are redacted without original host/URI error text. None
clients fail explicitly; ordinary mapping/cleanup errors are contained. Only
Exception is caught, not process interruption/BaseException. Real wiring must
use a read-only Atlas user for preview reads, not an existing write credential.
No live connection was made by these tests.
