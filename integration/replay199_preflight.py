"""Read-only capability/schema/index inspection. No permission/provisioning."""
from collections.abc import Mapping
from pymongo.write_concern import WriteConcern
from pymongo.read_concern import ReadConcern
from integration.replay199_schema import ReplayRefused,FAMILIES,source,validate_manifest

def inspect_archive(client,*,family,fingerprint=None):
 try:
  if family not in FAMILIES:raise ValueError()
  sn,an,identity,_=FAMILIES[family];required={sn:{'find','listIndexes','update'},an:{'find','listIndexes','insert'}}
  if family=='collector':required['collector_checkpoints197']={'find','listIndexes'}
  info=client.admin.command({'connectionStatus':1,'showPrivileges':True});hello=client.admin.command({'hello':1})
  if info.get('ok')!=1 or hello.get('ok')!=1 or not hello.get('setName')or hello.get('isWritablePrimary')is not True or type(hello.get('logicalSessionTimeoutMinutes'))is not int or hello['logicalSessionTimeoutMinutes']<1 or type(hello.get('maxWireVersion'))is not int or hello['maxWireVersion']<7:raise ValueError()
  auth=info['authInfo']
  if type(auth['authenticatedUsers'])is not list or len(auth['authenticatedUsers'])!=1 or type(auth['authenticatedUserPrivileges'])is not list or not 1<=len(auth['authenticatedUserPrivileges'])<=12:raise ValueError()
  got={name:set()for name in required}
  for g in auth['authenticatedUserPrivileges']:
   if type(g)is not dict or set(g)!={'resource','actions'}or type(g['resource'])is not dict or set(g['resource'])!={'db','collection'}or g['resource']['db']!='geo_intel'or g['resource']['collection']not in required or type(g['actions'])is not list or any(type(a)is not str for a in g['actions']):raise ValueError()
   name=g['resource']['collection']
   if not set(g['actions'])<=required[name]:raise ValueError()
   got[name].update(g['actions'])
  if got!=required:raise ValueError()
  handles={}
  for name in required:
   c=client['geo_intel'].get_collection(name,write_concern=WriteConcern(w='majority',j=True,wtimeout=5000),read_concern=ReadConcern('majority'))
   if c.name!=name or c.database.name!='geo_intel'or c.database.client is not client:raise ValueError()
   cursor=c.list_indexes(maxTimeMS=2000)
   try:
    indexes=[]
    for r in cursor:
     if not isinstance(r,Mapping)or len(r)>32 or len(indexes)>=16 or 'expireAfterSeconds'in r:raise ValueError()
     indexes.append(dict(r))
   finally:cursor.close()
   if not any(dict(r.get('key',{}))=={'_id':1}and not r.get('sparse',False)and 'partialFilterExpression'not in r for r in indexes):raise ValueError()
   handles[name]=c
  d=source(family,handles[sn].find_one({'_id':identity},max_time_ms=2000),fingerprint)
  genesis=handles[an].find_one({'_id':'batch:0'},max_time_ms=2000);validate_manifest(family,genesis)
  if genesis['epoch']!=0 or genesis['previous']!='0'*64:raise ValueError()
  if d['archive_epoch']==0 and d['chain_head']!=genesis['sha256']:raise ValueError()
  return {'source':handles[sn],'archive':handles[an],'checkpoints':handles.get('collector_checkpoints197'),'observed_capabilities_only':True,'archive_completeness_verified':False}
 except Exception:raise ReplayRefused('Read-only archive preflight unavailable; no writes')from None
