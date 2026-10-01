# Corrected preservation baseline, not deployable yet
Copyright (c) 2026 Push.

Supersedes the replacement RSS-only collection bundle. This baseline restores the original Geo/BRICS source behavior and only namespaces Python root imports. It retains RSS, optional full-text extraction, Google News, classification, duplicate filtering, reports, dashboards, stream configuration, Apps Script and original database functions. Retained source is not permission to activate sends, cleanup or public routes.

42 Python modules: non-import AST matches the pinned originals. 53 source/config/template/script files are mapped with original and copied hashes. Classifier, dedupe and extraction bytes are unchanged. Original bugs/limitations are not silently fixed in this baseline. The earlier draft's 57 tests do not certify this different baseline.

This is NOT a runnable merged application yet. Original environment names collide, Geo web connects on import, relative config paths need launch isolation or reviewed path adapters, and legacy routes lack the required private access wrapper. Old code is not imported or served during staging. Geo's unconfigured optional archive import remains as the original source rather than an invented shim. These gaps need exact reviewed integration changes.

Owner chose SAME existing database, no new database and no migration/copy. Existing approximately 10k articles are owner-reported; count/schema/IDs/indexes and database/collection names need verification. Do not overwrite/drop legacy records. Additive adapter/status/mapping collections need separate review. Connection URI may be entered directly by the user into Render; direct private access is optional, not required just to copy code.

Four-layer design in integration/cross-connections.json keeps existing features and proposes view/routing adapters instead of replacing the collection engine. Cross-links are still a design, not working implemented UI. Country/HSN/news relevance needs explicit mapping evidence; do not imply all articles match tariff codes.

Existing finder, Geo Render service, database and Apps Script triggers remain live and untouched. Staging has collection OFF and no deploy blueprint/auto-trigger. Before cutover: verify live service URL/config, inventory installed trigger IDs/handlers/properties, select a single collector/scheduler owner, reconcile storage counts/identities without a migration, test feature parity and private access, review exact changes, then switch once with rollback. Never install a second live collector alongside existing triggers.

Additive integration bridges now have 16 local fixture/preservation tests. They are not wired into the preserved finder screens or live news storage yet. Default private API denies all news access. Collection/mail/scraper remain OFF. Start staging only with gunicorn integration.private_router:app, never the retained legacy launchers.
