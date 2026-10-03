# In-memory writer fixture

This is a contract exercise only, not a Mongo adapter. It chooses no database,
collection name, unique index or live configuration. Geo and BRICS use separate
in-memory maps. No production migration or persistence is implied.

Identity is the exact supplied URL, with no normalization. Case, slashes and
whitespace can form distinct identities. Before a real writer is connected,
verify original collector URL handling and actual collection ownership/schema.
BRICS adds sha256(exact URL) as id. Supplied UTC collection stamps intentionally
replace the old naive-UTC BRICS convention and need reader compatibility review.

Field values are checked for plain JSON-like types, not per-field semantics:
score can be a string, published is unparsed. Bounds are per container rather
than a total-memory/DoS budget; large integers and empty extra keys are accepted.
Required strings must be nonblank; provider-owned fields are omitted.

The failed outcome is a caller-supplied synthetic fixture. It is not a real
storage failure classifier. A future Mongo adapter must separately test unique
indexes, concurrent duplicate races and partial bulk failures. No collector,
alert, mail, Telegram, scheduling, migration, drop or index operation is enabled.
