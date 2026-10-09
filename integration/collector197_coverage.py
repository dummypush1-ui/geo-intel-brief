"""Immutable version-2 input+source-coverage checkpoint, injected collection.
No client creation, provisioning, environment or owner permission. Version 1
adapter remains unchanged. Both hashes use typed, domain-separated encoding.
"""
import hashlib,json
from collector109_prep.checkpoint import digest,run_inputs,_freeze
from collector110_prep.durable_checkpoint import _encode,_decode,_encoded_budget
from collector110_prep.input_budget import capture
from collector110_prep.durable_checkpoint import DurableCheckpoints
from collector113_prep.feed_composition import original_catalog

class CoverageRefused(ValueError):pass
STATES=frozenset(('unstarted','selected','parsed_bozo_unverified','refused_timeout_or_budget','refused_global_cutoff','refused_envelope'))

def catalog_fingerprint():
    return hashlib.sha256(json.dumps(original_catalog(),separators=(',',':')).encode()).hexdigest()

def coverage(value):
    value=capture(value)['captured'];count=len(original_catalog())
    if type(value)is not dict or set(value)!={'catalog','source_states','all_sources_healthy'} or value['catalog']!=catalog_fingerprint() or value['all_sources_healthy']is not False:
        raise CoverageRefused('Exact catalog coverage required')
    rows=value['source_states']
    if type(rows)is not list or len(rows)!=count:
        raise CoverageRefused('Complete bounded source status required')
    for i,r in enumerate(rows):
        if type(r)is not dict or set(r)!={'index','state'} or type(r['index'])is not int or r['index']!=i or type(r['state'])is not str or r['state']not in STATES:
            raise CoverageRefused('Closed source status required')
    return value

def coverage_hash(key,fence,value):
    return hashlib.sha256(json.dumps(_freeze({'domain':'geo197c-source-coverage-v2','job':key,'fence':fence,'coverage':value}),ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

class CoverageCheckpoints:
    def __init__(self,collection):DurableCheckpoints(collection);self.c=collection
    def put(self,key,fence,inputs,source_coverage):
        try:
            self._identity(key,fence)
            bound=capture({'inputs':inputs,'coverage':source_coverage})['captured']
            v=bound['inputs']
            if type(v)is not dict or set(v)!={'candidates','active_categories','threshold'}:raise ValueError()
            v=run_inputs(v['candidates'],v['active_categories'],v['threshold']);c=coverage(bound['coverage'])
            row={'_id':key,'fence':str(fence),'version':2,'input_hash':digest(key,fence,v),
                'coverage_hash':coverage_hash(key,fence,c),'inputs':_encode(v),'coverage':_encode(c)}
            result=self.c.update_one({'_id':key},{'$setOnInsert':row},upsert=True)
            if result.acknowledged is not True:raise ValueError()
            saved=self.get(key,fence)
            if digest(key,fence,saved['inputs'])!=row['input_hash'] or coverage_hash(key,fence,saved['coverage'])!=row['coverage_hash']:raise ValueError()
            return {'input_hash':row['input_hash'],'coverage_hash':row['coverage_hash']}
        except Exception:raise CoverageRefused('Coverage checkpoint write unverifiable')from None
    def get(self,key,fence):
        try:
            self._identity(key,fence);row=self.c.find_one({'_id':key})
            if type(row)is not dict or set(row)!={'_id','fence','version','input_hash','coverage_hash','inputs','coverage'} or row['_id']!=key or row['fence']!=str(fence) or type(row['version'])is not int or row['version']!=2:raise ValueError()
            _encoded_budget(row['inputs']);_encoded_budget(row['coverage'])
            bound=capture({'inputs':_decode(row['inputs']),'coverage':_decode(row['coverage'])})['captured']
            v=bound['inputs']
            if type(v)is not dict or set(v)!={'candidates','active_categories','threshold'}:raise ValueError()
            v=run_inputs(v['candidates'],v['active_categories'],v['threshold']);c=coverage(bound['coverage'])
            if digest(key,fence,v)!=row['input_hash'] or coverage_hash(key,fence,c)!=row['coverage_hash']:raise ValueError()
            return {'inputs':v,'coverage':c}
        except Exception:raise CoverageRefused('Coverage checkpoint read unverifiable')from None
    @staticmethod
    def _identity(key,fence):
        if type(key)is not str or len(key)!=64 or any(c not in '0123456789abcdef'for c in key) or type(fence)is not int or fence<1:raise ValueError()
