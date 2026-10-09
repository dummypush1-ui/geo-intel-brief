"""Pure owner-review gate2 package. No database/client/env/files/network effects."""
import copy
from integration.native200_store import NAMES
from integration.native200_admission_preflight import VALIDATORS
from integration.replay199_schema import FAMILIES,manifest,source,ishash
SOURCES=[
 'https://www.mongodb.com/docs/manual/reference/command/create/',
 'https://www.mongodb.com/docs/manual/reference/command/insert/',
 'https://www.mongodb.com/docs/atlas/security-add-mongodb-roles/',
 'https://www.mongodb.com/docs/atlas/reference/custom-role-actions/',
 'https://www.mongodb.com/docs/manual/reference/command/listCollections/',
 'https://www.mongodb.com/docs/manual/core/schema-validation/specify-json-schema',
 'https://www.mongodb.com/docs/manual/core/transactions-production-consideration/'
]
def owner_package(*,fingerprint,clock):
 if not ishash(fingerprint)or type(clock)is not int or not 0<=clock<2**53:raise ValueError('Exact reviewed fingerprint/source clock required')
 if set(VALIDATORS)!=set(NAMES):raise ValueError('Exact all-eight schema set')
 role={'roleName':'geo_intel_native_runtime','inheritedRoles':[],'actions':[
  {'action':action,'resources':[{'db':'geo_intel','collection':n}for n in sorted(NAMES)]}for action in ('FIND','INSERT','UPDATE','LIST_INDEXES')
 ]+[{'action':'LIST_COLLECTIONS','resources':[{'db':'geo_intel','collection':''}]}]}
 # Request DATA only. Separate admin must choose create-vs-collMod after inventory.
 install=[{'collection':n,'create_if_verified_absent':{'create':n,'validator':copy.deepcopy(VALIDATORS[n]),'validationLevel':'strict','validationAction':'error','writeConcern':{'w':'majority','j':True,'wtimeout':5000}},'modify_if_existing_owner_reviewed':{'collMod':n,'validator':copy.deepcopy(VALIDATORS[n]),'validationLevel':'strict','validationAction':'error','writeConcern':{'w':'majority','j':True,'wtimeout':5000}}}for n in sorted(NAMES)]
 verify=[{'listCollections':1,'filter':{'name':n},'cursor':{'batchSize':2},'maxTimeMS':2000}for n in sorted(NAMES)]+[{'listIndexes':n,'cursor':{'batchSize':17},'maxTimeMS':2000}for n in sorted(NAMES)]
 genesis=[]
 for family in ('collector','broker'):
  sn,an,identity,_=FAMILIES[family];m=manifest(family,0,'0'*64,[])
  if family=='collector':d={'_id':identity,'schema':2,'revision':0,'fingerprint':fingerprint,'fence':0,'active':None,'history':[]}
  else:d={'_id':identity,'schema':3,'revision':0,'window_start':clock,'calls':0,'fence':0,'active':None,'last_clock':clock,'receipts':[]}
  d.update(archive_epoch=0,archived_count=0,chain_head=m['sha256']);source(family,d,fingerprint if family=='collector'else None)
  guard={'_id':family+':'+identity,'schema':1,'family':family,'serial':0,'operation':None,'phase':'idle'}
  genesis.extend([{'collection':sn,'empty_new_install_only':d},{'collection':an,'empty_new_install_only':m},{'collection':'native_guards200','empty_new_install_only':guard}])
 return {'state':'owner_review_only_not_executable','ready':False,'collection':False,'mail':False,'database':'geo_intel','role':role,'schema_requests':install,'readonly_verification_commands':verify,'empty_new_genesis_templates':genesis,'mandatory_holds':['NO execution without separate owner DB approval','NO genesis into existing nonempty/unknown state','NO generic schema migration or reset of calls/fences/active/history/receipts/journal serial','NO role creation-proof claim: INSERT itself permits collection creation','Owner-only DDL; no concurrent drop/schema change while native selected','Accepted ONE-write inspection/insert TOCTOU effect; next schema check holds, NOT zero-effect safety','NO activation: gate3 diagnostic, gate4 selection and ownerOKlive still open','Real Mongo validators/normalization/BSON/maxTimeMS/transactions/durability not measured'], 'sources':copy.deepcopy(SOURCES)}
