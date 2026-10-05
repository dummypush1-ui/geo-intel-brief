# Injected Geo sample probe, not hosted

probe_geo_sample is separate offline trusted injection. No env/route/startup
activation, scheduler/retry, original read-gate change or live query. Label:
read operations under a write-capable credential, not verified read-only access.
No privilege measurement. Intended operator env URI stays in Render, not chat,
logs, repository, response or raised ordinary exception.

Exactly geo_intel/articles, find {}, projection created_at/published/score and
_id0, created_atDESC, limit20, maxTimeMS2000. Bounded aggregate field compatibility
counts only; no values/IDs/articles/URI/host/error text returned. Empty distinct
from unavailable. Failures discard partial counts. Missing fields count missing,
unsupported inert values count incompatible. Custom objects/extra keys/oversized
strings/rows fail closed. published uses original-export zoned-string contract;
created_at uses current preview parse_dt (aware string<=40,UTCyear1970..2100).
BSON datetime created_at may be structurally inert but incompatible, never
coerced and marked compatible. score exact int/float finite +/-10^12.

Cursor/client close once on every owned path. Find failing before a cursor is
returned cannot close an unreturned cursor. Ordinary cleanup errors refuse result;
control BaseExceptions re-raised after both closes. Trusted factory externally
reviewed for bounded timeouts/TLS; probe passes serverSelection5s/connectFalse.
Existing create_geo_read_client meets defaults but Python facade is not privilege
isolation. Source malicious Python factories/provider hooks are not sandboxed.
Provider BSON allocation precedes scalar bounds; not wire-memory guarantee.
maxTimeMS/getMore/socket limits aren't one finite serving deadline.

9 native fake-driver tests pass. No real Mongo/Render check. Full schema/index,
explain/roles/snapshot/accounttransaction aren't established by samples. No
verified-source flag set. Dedicated read-only Atlas user preferred later; offer
click path only on request. Private manual hosted wrapper/auth/origin/CSRF/rate/
deadline/log review still needed before activation. No Free Render shell exists.

Any list/dict/ObjectId/Decimal128/bytes/custom value or string>100 in these three
projected fields refuses the WHOLE probe as unavailable; it is not counted as
incompatible. Supported inert wrong-format/date/null/bool/NaN values can count
incompatible. No claim every historical schema shape yields compatibilitycounts.

Fixed unavailable_reason distinguishes PyMongo ExecutionTimeout=query_timeout,
NetworkTimeout=io_timeout, ConnectionFailure(including selection timeout)=
connection_unavailable, ordinary other errors=source_unavailable, cleanup errors=
cleanup_unavailable. No source error/code/text emitted. Without PyMongo installed
classification falls back source_unavailable. created_at sorting may exceed2s
without an appropriate existing index; timeout is not connection refusal or
verified-empty. This probe never inspects/creates an index. Flag is precisely
probe_issues_no_writes=true, not a statement about credential or provider powers.
