import unittest,json,hashlib,copy
from integration.country_alerts import transition,safe_url
R={'owner':'fixture-owner','id':'rule-one','version':1,'countries':['India'],'risks':[],'categories':[]};LABELS=['India','USA']
def row(n=1,**kw):
 url='https://example.com/a'+str(n);r={'project':'geo','url':url,'article_key':hashlib.sha256(('geo\n'+url).encode()).hexdigest(),'title':'Fixture','summary':'','source':'Fixture','original_country':'India','risk_level':'HIGH','category':'TRADE','published_at':'old supplied value'};r.update(kw);return r
def source(rows,stamp='2026-10-06T00:00:00Z'):
 return {'status':'available','observed_at':stamp,'rows':rows,'sha256':hashlib.sha256(json.dumps(rows,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
class Tests(unittest.TestCase):
 def apply(self,state=None,rows=None,rule=R,**kw):return transition(state,rule,source(rows or []),LABELS,**kw)
 def test_baseline_new_repeat_changed_timestamp_independent(self):
  s=self.apply(rows=[row()])['state'];self.assertEqual(s['inbox'],[])
  out=self.apply(s,[row(),row(2)]);self.assertEqual(len(out['new_alerts']),1);s=out['state'];self.assertEqual(self.apply(s,[row(2,title='changed',risk_level='CRITICAL')])['new_alerts'],[])
  self.assertEqual(s['inbox'][0]['wording'],'newly seen in supplied sample, not newly published')
 def test_empty_unavailable_malformed_atomic(self):
  s=self.apply(rows=[row()])['state'];before=copy.deepcopy(s)
  for src in [{'status':'unavailable','observed_at':None,'rows':[],'sha256':None},source([row(article_key='0'*64)]),dict(source([]),sha256='forged')]:
   o=transition(s,R,src,LABELS);self.assertIn(o['status'],['refused','unavailable']);self.assertEqual(o['state'],s);self.assertEqual(s,before)
  s=self.apply(s,[])['state'];self.assertEqual(self.apply(s,[row()])['new_alerts'],[])
 def test_duplicates_conflict_unknown_no_alias(self):
  s=self.apply()['state'];self.assertEqual(len(self.apply(s,[row(),row()])['new_alerts']),1)
  self.assertEqual(self.apply(s,[row(),row(title='conflict')])['status'],'refused')
  self.assertEqual(self.apply(s,[row(original_country='IN'),row(2,risk_level='UNKNOWN')])['new_alerts'],[])
 def test_rule_change_explicit_fresh_baseline_version_only_no_replay(self):
  s=self.apply(rows=[row()])['state'];r=dict(R,countries=['USA'],version=2)
  self.assertEqual(self.apply(s,[row(2)],r)['status'],'refused');s=self.apply(s,[row(2)],r,operation='rebaseline')['state'];self.assertEqual(s['inbox'],[])
  self.assertEqual(self.apply(s,[row(2)],dict(r,version=3))['new_alerts'],[])
  self.assertEqual(self.apply(s,[],dict(r,version=0))['status'],'refused')
 def test_dismiss_reentry_and_output_aliasing(self):
  s=self.apply()['state'];out=self.apply(s,[row()]);a=out['new_alerts'][0]['id'];s=out['state'];dismiss=transition(s,R,None,LABELS,operation='dismiss',alert_id=a);self.assertEqual(dismiss['state']['inbox'][0]['state'],'dismissed');self.assertEqual(s['inbox'][0]['state'],'pending-review')
  s=self.apply(dismiss['state'],[])['state'];self.assertEqual(self.apply(s,[row()])['new_alerts'],[])
  out['new_alerts'][0]['article']['title']='tamper';self.assertEqual(out['state']['inbox'][0]['article']['title'],'Fixture')
 def test_cross_owner_id_and_invalid_clock(self):
  s=self.apply()['state']
  for r in [dict(R,owner='other'),dict(R,id='other')]:self.assertEqual(self.apply(s,[],r)['status'],'refused')
  self.assertEqual(transition(s,R,source([],stamp='not date'),LABELS)['state'],s)
 def test_capacity_atomic_and_redacted_query(self):
  s=self.apply()['state'];s['seen']=['geo:'+hashlib.sha256(str(i).encode()).hexdigest() for i in range(2000)]
  self.assertEqual(self.apply(s,[row()])['state'],s)
  url='https://example.com/a?token=secret&x=1';a=row(url=url,article_key=hashlib.sha256(('geo\n'+url).encode()).hexdigest());s=self.apply()['state'];o=self.apply(s,[a]);self.assertNotIn('secret',json.dumps(o));self.assertNotIn('?',o['state']['inbox'][0]['article']['url']);self.assertEqual(self.apply(o['state'],[a])['new_alerts'],[])
 def test_private_extra_and_hook_rejected(self):
  s=self.apply()['state'];self.assertEqual(self.apply(s,[row(backup_url='https://t.me/a')])['status'],'refused')
  class Evil(str):
   def __str__(self):raise AssertionError('hook')
  src=source([]);src['rows']=[row(title=Evil('evil'))];self.assertEqual(transition(s,R,src,LABELS)['status'],'refused')

 def test_all_state_invariants_read_dismiss(self):
  s=self.apply(self.apply()['state'],[row()])['state'];aid=s['inbox'][0]['id']
  for mutate in [lambda x:x.update(observed_at='!'),lambda x:x.update(version=-1),lambda x:x.update(initialized=False),lambda x:x['inbox'].append(copy.deepcopy(x['inbox'][0])),lambda x:x['inbox'][0].update(observed_at='2101-01-01T00:00:00+00:00'),lambda x:x['inbox'][0].update(observed_at='2026-10-07T00:00:00+00:00'),lambda x:x['inbox'][0]['article'].update(summary=[] )]:
   bad=copy.deepcopy(s);mutate(bad)
   for op in ['observe','read','dismiss']:self.assertEqual(transition(bad,R,source([]),LABELS,operation=op,alert_id=aid)['status'],'refused')
 def test_labels_urls_and_clock_rollback(self):
  s=self.apply()['state']
  self.assertEqual(transition(s,dict(R,countries=[' India ']),source([]),[' India ','USA'])['status'],'refused')
  for url in ['https://exa mple.com/a','https://example.com/a b']:
   with self.assertRaises(ValueError):safe_url(url)
  self.assertEqual(transition(s,R,source([],stamp='2026-10-05T00:00:00Z'),LABELS)['state'],s)
 def test_inbox_capacity_atomic_and_changed_rule_failure(self):
  s=self.apply()['state']
  for chunk in [range(100),range(100,200)]:s=self.apply(s,[row(i) for i in chunk])['state']
  self.assertEqual(len(s['inbox']),200);self.assertEqual(self.apply(s,[row(500)])['state'],s)
  changed=dict(R,countries=['USA'],version=2)
  for src in [{'status':'unavailable','rows':[],'observed_at':None,'sha256':None},dict(source([]),sha256='bad')]:
   o=transition(s,changed,src,LABELS,operation='rebaseline');self.assertEqual(o['state'],s)
  read=transition(s,R,None,LABELS,operation='read',alert_id=s['inbox'][0]['id']);self.assertEqual(read['state']['seen'],s['seen'])

 def test_normalized_utc_boundary_atomic_refusal(self):
  s=self.apply()['state']
  for stamp in ['1970-01-01T00:00:00+01:00','2100-12-31T23:30:00-01:00']:
   for old in [None,s]:
    out=transition(old,R,source([],stamp),LABELS);self.assertEqual(out['status'],'refused');self.assertEqual(out['state'],old)
