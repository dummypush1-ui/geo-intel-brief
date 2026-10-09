"""Strict fixed envelopes derived from current application document shapes.
Cross-field relationships, recursive typed encoding and hashes remain app checks.
No installation/provisioning or database effects.
"""
import copy
HASH={'bsonType':'string','pattern':'^[0-9a-f]{64}$'}
def integer(low=0,high=9007199254740991):return {'bsonType':['int','long'],'minimum':low,'maximum':high}
def obj(properties):return {'bsonType':'object','required':list(properties),'additionalProperties':False,'properties':properties}
def array(items,limit):return {'bsonType':'array','maxItems':limit,'items':items}
def nullable(schema):return {'oneOf':[{'bsonType':'null'},schema]}
I64=9223372036854775807
COUNTS={'bsonType':'object','additionalProperties':False,'maxProperties':8,'properties':{k:integer(0,1000)for k in ('fetched','prepared','attempted','inserted','duplicate','failed','uncertain')}}
JOB=obj({'key':HASH,'fence':integer(1,I64),'phase':{'enum':['accepted','running','fetch_complete','prepare_complete','write_started','completed','failed_before_write','uncertain_after_write']},'lease_until':integer(0,I64),'counts':COUNTS,'updated_at':integer(0,I64)})
# Typed nested arrays contain variable encoded scalar/list/dict/date content.
# Only their bounded top-level projection is a DB schema; _encoded_budget,
# capture/_decode and input+coverage hashes enforce recursive semantics.
ENCODED={'bsonType':'array','minItems':1,'maxItems':1000}
CP1=obj({'_id':HASH,'fence':{'bsonType':'string','pattern':'^[1-9][0-9]*$'},'hash':HASH,'version':{'enum':[1]},'inputs':ENCODED})
CP2=obj({'_id':HASH,'fence':{'bsonType':'string','pattern':'^[1-9][0-9]*$'},'version':{'enum':[2]},'input_hash':HASH,'coverage_hash':HASH,'inputs':ENCODED,'coverage':ENCODED})
CHECKPOINT={'oneOf':[CP1,CP2]}
RECEIPT=obj({'nonce_hash':HASH,'body_hash':HASH,'identity_hash':HASH,'fence':integer(1),'phase':{'enum':['reserved','send_started','complete','unknown_held']},'started_at':integer(),'deadline':integer(),'status':nullable(integer(200,599)),'response_hash':nullable(HASH),'response_bytes':integer(0,1048576)})
BUDGET_ACTIVE=obj({'key':HASH,'fence':integer(1),'started_at':integer(),'deadline':integer(),'phase':{'enum':['inflight','unknown_held']}})
EXTRA={'archive_epoch':integer(0,1024),'archived_count':integer(0,4096),'chain_head':HASH}
COLLECTOR=obj({'_id':{'enum':['geo108']},'schema':{'enum':[2]},'revision':integer(),'fingerprint':HASH,'fence':integer(0,I64),'active':nullable(JOB),'history':array(JOB,64),**EXTRA})
BROKER=obj({'_id':{'enum':['shared-finder-v1']},'schema':{'enum':[3]},'revision':integer(),'window_start':integer(),'calls':integer(0,60),'fence':integer(),'active':nullable(BUDGET_ACTIVE),'last_clock':integer(),'receipts':array(RECEIPT,64),**EXTRA})
REFERENCE=obj({'id':HASH,'sha256':HASH})
def archive(family):
 manifest=obj({'_id':{'bsonType':'string','pattern':'^batch:(0|[1-9][0-9]*)$'},'kind':{'enum':['manifest']},'family':{'enum':[family]},'epoch':integer(0,1024),'previous':HASH,'records':array(REFERENCE,64),'sha256':HASH})
 row=copy.deepcopy(JOB if family=='collector'else RECEIPT)
 row['properties']['phase']={'enum':['completed','failed_before_write']if family=='collector'else['complete']}
 record=obj({'_id':HASH,'kind':{'enum':['record']},'family':{'enum':[family]},'epoch':integer(1,1024),'source_revision':integer(),'fingerprint':HASH if family=='collector'else{'bsonType':'null'},'row':row,'checkpoint':nullable(CHECKPOINT)if family=='collector'else{'bsonType':'null'},'sha256':HASH})
 return {'$jsonSchema':{'oneOf':[manifest,record]}}
FIXED_VALIDATORS={'collector_jobs197':{'$jsonSchema':COLLECTOR},'finder_budget198':{'$jsonSchema':BROKER},'collector_replay199':archive('collector'),'finder_replay199':archive('broker'),'collector_checkpoints197':{'$jsonSchema':CHECKPOINT}}
