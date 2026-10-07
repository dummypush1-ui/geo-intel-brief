# Collector115 next composition outline, scratch only

Bind approved installation profile (hash-pinned original25 feeds/config defaults)
to114 fixed network worker,112 separate networkless parser, original selection
and111 durable checkpoint driver. Fetch and selection occur before write ticket.
Persist immutable candidates before any article write. No request URL/fence/source
flags/candidates/writer accepted. Source failure is explicit partial/error status,
not fictitious all-feeds health. Per-feed output/candidate limits and whole-run
budget required; deterministic source order retained. Original classification /
dedupe/categories run before writer. Default MAX_ITEMS_PER_FEED40 is inside100
parser projection, but environment values>100 must be refused as unsupported,
never silently truncated or labelled full parity. Original feed entries[:limit]
semantics remain, not limit on accepted rows.

Optional full text/GNews/Telegram backup require explicit separate adapters;
production flag true without adapter must fail closed at profile boot, not silently
turn feature off. While disabled, flags remain reported as disabled_by_config.
Original defaults: fulltext=false, gnews=false, Telegrambackup=true. Thus ordinary
production default requires a working backup adapter before full-feature cutover;
preparation cannot call itself complete merely because optional flags are off.

Production mount still OFF. Source profile validation is NOT owner permission,
actual Mongo role/index/TTL proof, runtime viability, or scheduler/cutover approval.
