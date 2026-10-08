# Copyright (c) 2026 Push. All rights reserved.
"""Separate supplied government observations, not news/public article records.

Pure query interface and proposed isolated collection contract. No client,
roles, indexes, route registration, production writes or deletion effects.
"""
from copy import deepcopy
import re
from .core import MAX_ROWS, text


def storage_plan(database, collection):
    for name in (database, collection):
        if type(name) is not str or not re.fullmatch(r'[a-z][a-z0-9_]{2,63}', name) or name.startswith('system'):
            raise ValueError('Explicit reviewed resource names required')
    if collection in {'articles', 'events', 'mail_control', 'mail_receipts',
                      'full_records', 'collection_outbox', 'collection_control', 'backup_journal'}:
        raise ValueError('Government observations must use isolated resource')
    return {'scope': 'proposal_not_provisioned', 'database': database,
            'collection': collection, 'schema': 'india_government_snapshot_v1',
            'index_proposals': [{'keys':[('dataset_id',1)], 'unique':True}],
            'ttl_indexes':[], 'automatic_deletion':False, 'live_mapping_verified':False,
            'provision_allowed':False, 'write_strategy':'replace_complete_dataset_snapshot_atomically',
            'retention':'preserve_old_on_partial_failed_or_unknown_pull',
            'mount_required':True}


class GovernmentDataReader:
    """Caller supplies a bounded snapshot mapping from its reviewed store.

    Exact matching only; published district text is not assumed an LGD entity.
    Missing dataset and empty match are distinct. Freshness is dataset_date,
    not HTTP capture time. No external store/project selection occurs here.
    """
    def __init__(self, snapshots):
        if type(snapshots) is not dict or len(snapshots)>100:
            raise ValueError('Bounded plain snapshot map required')
        total=0
        for key, snapshot in snapshots.items():
            text(key,80)
            if type(snapshot) is not dict or snapshot.get('state')!='complete' or type(snapshot.get('records')) is not list:
                raise ValueError('Complete supplied snapshot shape required')
            total+=len(snapshot['records'])
            if len(snapshot['records'])>MAX_ROWS or total>MAX_ROWS:
                raise ValueError('Snapshot read bound exceeded')
            for row in snapshot['records']:
                if type(row) is not dict or row.get('dataset_id')!=key or type(row.get('geography')) is not dict:
                    raise ValueError('Matching government rows required')
        self._snapshots=deepcopy(snapshots)

    def read(self, dataset_id, *, metric=None, state=None, district=None, period=None, limit=100):
        dataset_id=text(dataset_id,80)
        if type(limit) is not int or not 1<=limit<=1000:
            raise ValueError('Bounded read limit required')
        filters={k:text(v) for k,v in {'metric':metric,'state':state,'district':district,'period':period}.items() if v is not None}
        snapshot=self._snapshots.get(dataset_id)
        if snapshot is None:
            return {'state':'unavailable','records':[],'matched':0,'truncated':False,'captured_at':None}
        matched=[]
        for row in snapshot['records']:
            values={'metric':row.get('metric'),'period':row.get('period'),
                    'state':row['geography'].get('state'),'district':row['geography'].get('district')}
            if all(values[k]==v for k,v in filters.items()):matched.append(row)
        return {'state':'available','records':deepcopy(matched[:limit]),'matched':len(matched),
                'truncated':len(matched)>limit,'captured_at':snapshot.get('captured_at')}
