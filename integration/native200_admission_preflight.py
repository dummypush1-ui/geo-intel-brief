"""Fixed read-only collection/index inspection, no provisioning mutation."""
from integration.native200_admission_store import AdmissionStore as NativeStore
from integration.native200_transactions import NativeRefused
# Journal validators exact, strict/error; gate2 installs them, never this code.
VALIDATORS={
 'native_guards200':{'$jsonSchema':{'bsonType':'object','required':['_id','schema','family','serial','operation','phase'],'additionalProperties':False,'properties':{'_id':{'bsonType':'string'},'schema':{'enum':[1]},'family':{'enum':['collector','broker']},'serial':{'bsonType':['int','long'],'minimum':0,'maximum':4096},'operation':{'bsonType':['string','null']},'phase':{'enum':['idle','reserved','commit_attempt','acknowledged','admission_attempt']}}}},
 'native_operations200':{'$jsonSchema':{'bsonType':'object','required':['_id','schema','guard','serial','plan'],'additionalProperties':False,'properties':{'_id':{'bsonType':'string'},'schema':{'enum':[1]},'guard':{'bsonType':'string'},'serial':{'bsonType':['int','long'],'minimum':1,'maximum':4096},'plan':{'bsonType':'object','additionalProperties':False,'required':['family','source','expected_revision','epoch','head','after_hash'],'properties':{'family':{'enum':['collector','broker']},'source':{'enum':['geo108','shared-finder-v1']},'expected_revision':{'bsonType':['int','long'],'minimum':0,'maximum':9007199254740991},'epoch':{'bsonType':['int','long'],'minimum':0,'maximum':1024},'head':{'bsonType':'string','pattern':'^[0-9a-f]{64}$'},'after_hash':{'bsonType':'string','pattern':'^[0-9a-f]{64}$'}}}}}},
 'native_outcomes200':{'$jsonSchema':{'bsonType':'object','required':['_id','schema','guard','serial','plan_hash','after_hash'],'additionalProperties':False,'properties':{'_id':{'bsonType':'string'},'schema':{'enum':[1]},'guard':{'bsonType':'string'},'serial':{'bsonType':['int','long'],'minimum':1,'maximum':4096},'plan_hash':{'bsonType':'string'},'after_hash':{'bsonType':'string'}}}}
}
OUTCOME_VALIDATOR=VALIDATORS['native_outcomes200']
CLOSURE_SCHEMA={'bsonType':'object','required':['_id','kind','schema','guard','old_operation','old_serial','new_operation','new_serial','source_hash'],'additionalProperties':False,'properties':{'_id':{'bsonType':'string','pattern':'^admission:[0-9a-f]{64}$'},'kind':{'enum':['admission']},'schema':{'enum':[1]},'guard':{'enum':['collector:geo108','broker:shared-finder-v1']},'old_operation':{'bsonType':'string','pattern':'^[0-9a-f]{64}$'},'old_serial':{'bsonType':['int','long'],'minimum':1,'maximum':4095},'new_operation':{'bsonType':'string','pattern':'^[0-9a-f]{64}$'},'new_serial':{'bsonType':['int','long'],'minimum':2,'maximum':4096},'source_hash':{'bsonType':'string','pattern':'^[0-9a-f]{64}$'}}}
VALIDATORS['native_outcomes200']={'$or':[OUTCOME_VALIDATOR,{'$jsonSchema':CLOSURE_SCHEMA}]}
from integration.native201_schemas import FIXED_VALIDATORS
VALIDATORS.update(FIXED_VALIDATORS)
def inspect_admission_existing(store):
 if type(store)is not NativeStore:raise NativeRefused('Exact inspection store')
 out=store._command({'listCollections':1,'filter':{'name':store.name},'cursor':{'batchSize':2},'maxTimeMS':2000})
 cursor=out.get('cursor',{})
 if type(cursor)is not dict:raise NativeRefused('Exact inspection cursor')
 if cursor.get('id')!=0 or cursor.get('ns')!='geo_intel.$cmd.listCollections'or type(cursor.get('firstBatch'))is not list or len(cursor['firstBatch'])!=1:raise NativeRefused('Existing collection inspection held')
 row=cursor['firstBatch'][0]
 if type(row)is not dict:raise NativeRefused('Exact inspection row')
 if row.get('name')!=store.name or row.get('type')!='collection':raise NativeRefused('Exact existing collection required')
 if store.name in VALIDATORS:
  opts=row.get('options',{})
  if type(opts)is not dict:raise NativeRefused('Exact inspection options')
  if opts.get('validator')!=VALIDATORS[store.name]or opts.get('validationLevel','strict')!='strict'or opts.get('validationAction','error')!='error':raise NativeRefused('Exact mapping validator required')
 out=store._command({'listIndexes':store.name,'cursor':{'batchSize':17},'maxTimeMS':2000});cursor=out.get('cursor',{})
 if type(cursor)is not dict:raise NativeRefused('Exact index cursor')
 rows=cursor.get('firstBatch')
 if cursor.get('id')!=0 or cursor.get('ns')!='geo_intel.'+store.name or type(rows)is not list or not 1<=len(rows)<=16:raise NativeRefused('Bounded exhausted index inspection')
 if any(type(r)is not dict or 'expireAfterSeconds'in r for r in rows):raise NativeRefused('No TTL allowed')
 if not any(r.get('key')=={'_id':1}and r.get('name')=='_id_'and not r.get('sparse')and not r.get('partialFilterExpression')and r.get('unique',True)is True for r in rows):raise NativeRefused('Ordinary unique identity index required')
 return True
