# Collector115 installed profile and supplied catalog composition

INACTIVE. Production OFF. No real fetch call, runtime mount, DB client/write,
mail, Telegram or trigger changes. Fixed-source original config defaults loaded
through hash-pinned AST, never by importing dotenv/client config. Original25 feed
catalog, MAX_ITEMS_PER_FEED40, timeout20, lookback48, all categories, dedupe.85.
Explicit installation override shape only. Unknown/secret/URL overrides refused.
Fulltext/GNews false and Telegrambackup true defaults retained and reported.
Enabled missing adapters are pending gates, never silently turned off.

Bounded supplied body/hash/wire evidence by catalog URL -> isolated112 parser ->
original hash-pinned selection -> aggregate capture -> immutable111 checkpoint
input shape. Original catalog order preserved even if input mapping order differs.
Missing feeds are not_supplied, not healthy/empty success. Bozo, entry/projection
counts and date fallbacks retained.100 projection cap / maxitems bounded<=100;
original default40 supported, larger environment values refused as unsupported,
not silently truncated.4MiB aggregate supplied bodies,1000 candidates and110's
2MiB/nodes/depth capture caps. No actual network fetch integration in this stage.

14 tests cover defaults/flags/refusals, body hash, real isolated parser/original
selection, cutoff/default clock/unknown timezone, firstN vs firstNvalid, order,
then111 durable fixture checkpoint+GeoFixtureStore drive. Last is a fixture write,
not real DB proof. Profile's pending_gates and live_write_ready=False are retained.
Existing adapters have their inherited limits; the full-source failure/cycle,
fulltext/GNews/Telegram, real writer/service and live deployment gates remain.
