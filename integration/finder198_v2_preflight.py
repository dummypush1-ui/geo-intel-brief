"""Read-only v2 preflight. No client/migration/rolegrant; v1 remainsunchanged."""
from integration.finder198_budget import BudgetRefused,ID
from integration.finder198_receipts import _v2
def inspect_budget_v2(client):
 """Read-only exact dedicated role/mapping/state preflight. No provisioning.
  This observes capabilities, not owner permission. No client creation here.
 """
 try:
  from pymongo.write_concern import WriteConcern
  from pymongo.read_concern import ReadConcern
  info=client.admin.command({'connectionStatus':1,'showPrivileges':True});hello=client.admin.command({'hello':1})
  if info.get('ok')!=1 or hello.get('ok')!=1 or not hello.get('setName')or hello.get('isWritablePrimary')is not True:raise ValueError()
  auth=info['authInfo']
  if type(auth['authenticatedUsers'])is not list or len(auth['authenticatedUsers'])!=1:raise ValueError()
  grants=auth['authenticatedUserPrivileges'];got=set()
  if type(grants)is not list or not 1<=len(grants)<=4:raise ValueError()
  for g in grants:
   if type(g)is not dict or set(g)!={'resource','actions'}or g['resource']!={'db':'geo_intel','collection':'finder_budget198'}or type(g['actions'])is not list or any(type(a)is not str for a in g['actions']):raise ValueError()
   got.update(g['actions'])
  if got!={'find','listIndexes','update'}:raise ValueError()
  c=client['geo_intel'].get_collection('finder_budget198',write_concern=WriteConcern(w='majority',j=True,wtimeout=5000),read_concern=ReadConcern('majority'))
  rows=c.list_indexes(maxTimeMS=2000)
  try:
   indexes=list(rows)
   if not 1<=len(indexes)<=16 or any('expireAfterSeconds'in r for r in indexes)or not any(dict(r.get('key',{}))=={'_id':1}and 'partialFilterExpression'not in r for r in indexes):raise ValueError()
  finally:rows.close()
  _v2(c.find_one({'_id':ID},max_time_ms=2000))
  return c
 except Exception:raise BudgetRefused('Dedicated budget preflight unavailable; no writes')from None
