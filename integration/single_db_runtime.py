"""Offline preview composition using an explicit one-DB/two-collection plan.

Not selected by private_router or compose. Caller injects a fixture client
factory; there is no default MongoClient import. Reads can occur only if a
caller later wires and enables this composition after the separate live gate.
"""
from integration.single_db_plan import SingleDatabasePlan
from integration.preview_access import create_preview_from_env
from integration.storage_reader import ReadOnlyNewsReader


def compose_single_database(environ, plan, client_factory):
    if type(environ) is not dict or any(type(k) is not str or type(v) is not str
                                       for k, v in environ.items()):
        raise ValueError('Exact supplied environment map required')
    if type(plan) is not SingleDatabasePlan:
        raise ValueError('Exact reviewed single database plan required')
    # Access validation happens before creating a client, even with reads off.
    app = create_preview_from_env(environ)
    clients = []
    if environ.get('NEWS_READ_ENABLED', 'false').lower() == 'true':
        if environ.get('PREVIEW_ACCESS_ENABLED', 'false').lower() != 'true':
            raise ValueError('Private preview access required')
        if environ.get('NEWS_STORE_MAPPING_VERIFIED', 'false').lower() != 'true':
            raise ValueError('Store review required')
        uri = environ.get('GEO_MONGODB_URI', '')
        if not uri:
            raise ValueError('Explicit Geo database URI required')
        if not callable(client_factory):
            raise ValueError('Explicit fixture client factory required')
        try:
            client = client_factory(uri, serverSelectionTimeoutMS=5000, connect=False)
        except Exception:
            raise ValueError('Read-only client creation failed') from None
        if client is None:
            raise ValueError('Read-only client unavailable')
        clients.append(client)
        try:
            database = client[plan.database]
            stores = {'geo': database[plan.geo_articles], 'brics': database[plan.other_articles]}
            reader = ReadOnlyNewsReader(stores, verified=True, limit=100)
            app = create_preview_from_env(environ, reader=reader)
        except Exception:
            try:
                client.close()
            except Exception:
                pass
            raise ValueError('Read-only collection mapping failed') from None
    app.extensions['read_only_news_clients'] = clients
    app.extensions['single_database_plan'] = plan
    return app
