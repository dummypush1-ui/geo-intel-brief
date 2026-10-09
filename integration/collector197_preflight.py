"""Read-only live Mongo preflight candidate; no client creation or provisioning.
Only called explicitly by a later default-OFF composition. Command results prove
observed capabilities, never user authority to write. Generic errors only.
"""
from collections.abc import Mapping
from integration.collector197_orchestrator import _concerns
from collector108_prep.durable_ledger import DurableLedger

class PreflightRefused(ValueError):
    pass

NAMES = ('articles', 'collector_jobs197', 'collector_checkpoints197')
REQUIRED = {'articles': {'find', 'listIndexes', 'insert'},
            'collector_jobs197': {'find', 'listIndexes', 'update'},
            'collector_checkpoints197': {'find', 'listIndexes', 'update', 'insert'}}
# Checkpoints need insert for new immutable upsert documents; ledger is preinitialized.
# No collection creation allowed by this adapter, including initialization.

def inspect_writer(client, fingerprint):
    handles = {}
    try:
        if type(fingerprint) is not str or len(fingerprint) != 64 or any(c not in '0123456789abcdef' for c in fingerprint):
            raise ValueError()
        info = client.admin.command({'connectionStatus': 1, 'showPrivileges': True})
        hello = client.admin.command({'hello': 1})
        if info.get('ok') != 1 or hello.get('ok') != 1 or not hello.get('setName') or hello.get('isWritablePrimary') is not True:
            raise ValueError()
        auth = info['authInfo']
        if type(auth['authenticatedUsers']) is not list or len(auth['authenticatedUsers']) != 1:
            raise ValueError()
        grants = auth['authenticatedUserPrivileges']
        if type(grants) is not list or not 1 <= len(grants) <= 12:
            raise ValueError()
        got = {name: set() for name in NAMES}
        for grant in grants:
            if type(grant) is not dict or set(grant) != {'resource','actions'}:
                raise ValueError()
            resource = grant['resource']; actions = grant['actions']
            if (type(resource) is not dict or set(resource) != {'db','collection'}
                    or resource['db'] != 'geo_intel' or resource['collection'] not in NAMES
                    or type(actions) is not list or any(type(a) is not str for a in actions)):
                raise ValueError()
            name = resource['collection']
            if not set(actions) <= REQUIRED[name]:
                raise ValueError()
            got[name].update(actions)
        if got != REQUIRED:
            raise ValueError()
        from pymongo.write_concern import WriteConcern
        from pymongo.read_concern import ReadConcern
        db = client['geo_intel']
        for name in NAMES:
            c = db.get_collection(name, write_concern=WriteConcern(w='majority',j=True,wtimeout=5000),
                                  read_concern=ReadConcern('majority'))
            if c.name != name or c.database.name != 'geo_intel' or c.database.client is not client:
                raise ValueError()
            _concerns(c)
            cursor = c.list_indexes(maxTimeMS=2000)
            try:
                indexes = []
                for row in cursor:
                    if not isinstance(row, Mapping) or len(row) > 32 or len(indexes) >= 64 or 'expireAfterSeconds' in row:
                        raise ValueError()
                    indexes.append(dict(row))
            finally:
                cursor.close()
            if not indexes:
                raise ValueError()
            if name == 'articles':
                valid = [r for r in indexes if dict(r.get('key',{})) == {'url':1}
                         and r.get('unique') is True and r.get('sparse',False) is False
                         and 'partialFilterExpression' not in r
                         and r.get('collation') == {'locale':'simple'}]
                if not valid:
                    raise ValueError()
            # Existing _id unique constraint is mandatory for ledger/checkpoint.
            elif not any(dict(r.get('key',{})) == {'_id':1} and 'partialFilterExpression' not in r for r in indexes):
                raise ValueError()
            handles[name] = c
        ledger = DurableLedger(handles['collector_jobs197'], 'geo108', fingerprint)
        # Validate the existing full document without mutation/initialization.
        from collector108_prep.durable_ledger import _valid_document
        _valid_document(handles['collector_jobs197'].find_one({'_id':'geo108'}, max_time_ms=2000), 'geo108', fingerprint)
        return {'ledger':ledger, 'articles':handles['articles'],
                'checkpoints':handles['collector_checkpoints197'],
                'role_index_ttl_observed':True}
    except Exception:
        raise PreflightRefused('Writer preflight unavailable; no writes permitted') from None
