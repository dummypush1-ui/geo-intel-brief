"""Read-only live Mongo preflight candidate; no client creation or provisioning.
Only called explicitly by a later default-OFF composition. Command results prove
observed capabilities, never user authority to write. Generic errors only.
"""
from collections.abc import Mapping
from integration.collector197_orchestrator import _concerns
from collector108_prep.durable_ledger import DurableLedger

class PreflightRefused(ValueError):
    pass

class PreflightConnectRefused(PreflightRefused):
    pass

class PreflightRoleRefused(PreflightRefused):
    pass

class PreflightIndexRefused(PreflightRefused):
    pass

class PreflightLedgerRefused(PreflightRefused):
    pass

# Closed connect-group condition vocabulary shared with collector197_job and
# collector_actions/entry. Constant condition labels and driver/OS class names
# only: never messages, server values, hosts, URIs or credentials.
CONNECT_PREDICATES=frozenset({'fingerprint','status_command','hello_command','hello_ok','hello_setName','hello_primary'})
CONNECT_UNDERLYING=frozenset({'ServerSelectionTimeoutError','ConnectionFailure','AutoReconnect','NetworkTimeout','OperationFailure','ConfigurationError','ExecutionTimeout','OSError','SSLError','gaierror','TimeoutError','ConnectionError'})

def _connect_refused(predicate, src=None):
    e = PreflightConnectRefused('Writer preflight unavailable; no writes permitted')
    e.connect_predicate = predicate
    if src is not None:
        n = type(src).__name__
        e.connect_underlying = n if n in CONNECT_UNDERLYING else 'other'
    return e

NAMES = ('articles', 'collector_jobs197', 'collector_checkpoints197')
REQUIRED = {'articles': {'find', 'listIndexes', 'insert'},
            'collector_jobs197': {'find', 'listIndexes', 'update'},
            'collector_checkpoints197': {'find', 'listIndexes', 'update', 'insert'}}
# Checkpoints need insert for new immutable upsert documents; ledger is preinitialized.
# No collection creation allowed by this adapter, including initialization.

def _simple_collation(row):
    # MongoDB does not persist {locale: 'simple'} and lists binary comparison as an
    # ABSENT collation field (some 9.0.x builds listed exactly {locale: 'simple'}).
    # Any other present value (None, {}, extra keys, other locales) is refused.
    if 'collation' not in row:
        return True
    c = row['collation']
    return isinstance(c, dict) and c == {'locale': 'simple'}


def inspect_writer(client, fingerprint, role_policy='exact'):
    # 'exact' is the default least-privilege contract and stays unchanged.
    # 'coverage_admin_accepted' accepts whatever wider credential envelope the
    # credential holds: a minimum capability floor ONLY, never least privilege.
    # Unknown policy values refuse closed before any command runs.
    if role_policy not in ('exact', 'coverage_admin_accepted'):
        raise ValueError()
    handles = {}
    try:
        try:
            if type(fingerprint) is not str or len(fingerprint) != 64 or any(c not in '0123456789abcdef' for c in fingerprint):
                raise _connect_refused('fingerprint')
            try:
                info = client.admin.command({'connectionStatus': 1, 'showPrivileges': True})
            except Exception as e:
                raise _connect_refused('status_command', e)
            try:
                hello = client.admin.command({'hello': 1})
            except Exception as e:
                raise _connect_refused('hello_command', e)
            if info.get('ok') != 1:
                raise _connect_refused('status_command')
            if hello.get('ok') != 1:
                raise _connect_refused('hello_ok')
            if not hello.get('setName'):
                raise _connect_refused('hello_setName')
            if hello.get('isWritablePrimary') is not True:
                raise _connect_refused('hello_primary')
        except PreflightConnectRefused as e:
            raise e from None
        except Exception as e:
            raise _connect_refused('other', e) from None
        try:
            auth = info['authInfo']
            if type(auth['authenticatedUsers']) is not list or len(auth['authenticatedUsers']) != 1:
                raise ValueError()
            grants = auth['authenticatedUserPrivileges']
            if type(grants) is not list or not 1 <= len(grants) <= (12 if role_policy == 'exact' else 64):
                raise ValueError()
            got = {name: set() for name in NAMES}
            for grant in grants:
                if type(grant) is not dict or set(grant) != {'resource','actions'}:
                    raise ValueError()
                resource = grant['resource']; actions = grant['actions']
                if type(resource) is not dict or type(actions) is not list or any(type(a) is not str for a in actions):
                    raise ValueError()
                keys = set(resource)
                if role_policy == 'exact':
                    if (keys != {'db','collection'}
                            or resource['db'] != 'geo_intel' or resource['collection'] not in NAMES):
                        raise ValueError()
                    name = resource['collection']
                    if not set(actions) <= REQUIRED[name]:
                        raise ValueError()
                    got[name].update(actions)
                else:
                    # Coverage over documented resource shapes for the 3 named
                    # non-system collections in geo_intel. {cluster: true} grants
                    # system-state actions only and NEVER counts as collection
                    # coverage. 64 is an application anomaly bound on expanded
                    # grants, not a documented MongoDB maximum.
                    if keys == {'db','collection'}:
                        db, coll = resource['db'], resource['collection']
                        if type(db) is not str or type(coll) is not str:
                            raise ValueError()
                        if db in ('geo_intel','') and (coll == '' or coll in NAMES):
                            targets = NAMES if coll == '' else (coll,)
                            for name in targets:
                                got[name].update(a for a in actions if a in REQUIRED[name])
                    elif keys == {'anyResource'} and resource['anyResource'] is True:
                        for name in NAMES:
                            if 'anyAction' in actions:
                                got[name].update(REQUIRED[name])
                            else:
                                got[name].update(a for a in actions if a in REQUIRED[name])
                    elif keys == {'cluster'} and resource['cluster'] is True:
                        pass
                    else:
                        raise ValueError()
            if got != REQUIRED:
                raise ValueError()
        except Exception:
            raise PreflightRoleRefused('Writer preflight unavailable; no writes permitted') from None
        try:
            from pymongo.write_concern import WriteConcern
            from pymongo.read_concern import ReadConcern
            from pymongo import timeout as _timeout
            db = client['geo_intel']
            for name in NAMES:
                c = db.get_collection(name, write_concern=WriteConcern(w='majority',j=True,wtimeout=5000),
                                      read_concern=ReadConcern('majority'))
                if c.name != name or c.database.name != 'geo_intel' or c.database.client is not client:
                    raise ValueError()
                _concerns(c)
                with _timeout(2):
                    cursor = c.list_indexes()
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
                             and _simple_collation(r)]
                    if not valid:
                        raise ValueError()
                # Existing _id unique constraint is mandatory for ledger/checkpoint.
                elif not any(dict(r.get('key',{})) == {'_id':1} and 'partialFilterExpression' not in r for r in indexes):
                    raise ValueError()
                handles[name] = c
        except Exception:
            raise PreflightIndexRefused('Writer preflight unavailable; no writes permitted') from None
        try:
            ledger = DurableLedger(handles['collector_jobs197'], 'geo108', fingerprint)
            # Validate the existing full document without mutation/initialization.
            from collector108_prep.durable_ledger import _valid_document
            _valid_document(handles['collector_jobs197'].find_one({'_id':'geo108'}, max_time_ms=2000), 'geo108', fingerprint)
        except Exception:
            raise PreflightLedgerRefused('Writer preflight unavailable; no writes permitted') from None
        return {'ledger':ledger, 'articles':handles['articles'],
                'checkpoints':handles['collector_checkpoints197'],
                'role_index_ttl_observed':True}
    except PreflightRefused:
        raise
    except Exception:
        raise PreflightRefused('Writer preflight unavailable; no writes permitted') from None
