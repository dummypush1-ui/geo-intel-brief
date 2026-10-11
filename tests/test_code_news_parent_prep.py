import unittest
from unittest.mock import patch
from integration.news_pages import WholeGeoPages,PageExpired
from integration.public_live_builder import sanitize_public_geo_rows
from integration.news_api import create_app
from integration.code_news_links import Links
from integration.code_news_parent_prep import Broker,Admission,ResolveQuota
from tests.test_news_pages185 import Store,rows,F
T=dict(system='HS',edition='2022',code='8517',description='Phones')
P={k:T[k]for k in ('system','edition','code')}
class Tests(unittest.TestCase):
 def make(self,n=105):
  self.now=0;self.store=Store(rows(n));self.p=WholeGeoPages(self.store,sanitize_public_geo_rows,verified=True,clock=lambda:self.now,start_cleaner=False);self.addCleanup(self.p.close)
  self.m=Links([T],[]);self.b=Broker(self.p,self.m,'a'*64,'v1',resolve_quota=ResolveQuota());return self.b
 def next(self,r,**kw):return self.b.page(scope=r['scope'],manifest='a'*64,matcher_version='v1',**kw)
 def test_HEAD_no_index_reader_lock(self):
  b=self.make();self.p.lock.acquire()
  try:
   with patch.object(self.m,'resolve',side_effect=AssertionError('index')):self.assertEqual(b.head()[1],200)
  finally:self.p.lock.release()
  self.assertEqual(self.store.calls,[]);self.assertEqual(b.ledger.rows,{})
 def test_unknown_target_no_parent(self):
  b=self.make();r,status=b.page(dict(P,code='9999'));self.assertEqual(status,200);self.assertEqual(r['state'],'target_unavailable');self.assertEqual(self.store.calls,[])
 def test_real_map_formula_12News4D(self):
  b=self.make(200)
  for _ in range(12):self.p.page(F)
  for _ in range(4):self.assertEqual(b.page(P)[1],200)
  self.assertEqual(len(self.p.streams),16);self.assertEqual(b.ledger.total(),16);self.assertEqual(len(b.ledger.rows),4)
  self.assertEqual(b.page(P)[1],429)
  from integration.news_pages import PageBusy
  with self.assertRaises(PageBusy):self.p.page(F)
 def test_first_EOF_Dkeeps_slot_and_four_blocks(self):
  b=self.make(1)
  for _ in range(4):self.assertEqual(b.page(P)[1],200)
  self.assertEqual(self.p.streams,{});self.assertEqual(b.ledger.total(),4);self.assertEqual(len(b.ledger.rows),4);self.assertEqual(b.page(P)[1],429)
  self.now=120;self.assertEqual(b.page(P)[1],200);self.assertEqual(b.ledger.total(),1)
 def test_token_EOF_parent_retained_count_once(self):
  b=self.make(105);a,_=b.page(P);self.assertEqual(b.ledger.total(),1);r,status=self.next(a)
  self.assertEqual(status,200);self.assertTrue(r['scan_complete']);self.assertEqual(len(self.p.streams),1);self.assertEqual(b.ledger.total(),1)
  calls=len(self.store.calls);again,_=self.next(a);self.assertEqual(r,again);self.assertEqual(len(self.store.calls),calls)
 def test_manifest_and_matcher_drift_410_owned_release(self):
  for fields in [dict(manifest='b'*64,matcher_version='v1'),dict(manifest='a'*64,matcher_version='v2')]:
   b=self.make();a,_=b.page(P);r,status=b.page(scope=a['scope'],**fields);self.assertEqual(status,410);self.assertEqual(b.ledger.total(),0);self.assertEqual(self.p.streams,{})
 def test_parent_expiry_Dcarry_clear_410_once(self):
  b=self.make(200);a,_=b.page(P);self.now=120
  with self.p.lock:self.p._expire()
  self.assertEqual(b.ledger.total(),0);self.assertEqual(self.store.cursors[0].closed,1)
  self.assertEqual(self.next(a)[1],410);self.assertEqual(self.next(a)[1],410);self.assertEqual(self.store.cursors[0].closed,1)
 def test_shutdown_clears_streams_and_reservations(self):
  b=self.make(1);b.page(P);self.assertEqual(b.ledger.total(),1);self.p.close();self.assertEqual(b.ledger.total(),0);self.assertEqual(b.ledger.rows,{})
 def test_replay_cannot_hold_beyond1800(self):
  b=self.make(105);a,_=b.page(P);self.next(a)
  for now in range(100,1800,100):self.now=now;self.assertEqual(self.next(a)[1],200)
  self.now=1800;self.assertEqual(self.next(a)[1],410);self.assertEqual(b.ledger.total(),0)
 def test_News_endpoint_scope_refusal_stays409(self):
  b=self.make(200);a,_=b.page(P);parent=next(iter(self.p.streams.values()));token=parent['next'];before=parent['offset']
  c=create_app(full_news_pages=self.p,authorize=lambda _:True).test_client();self.assertEqual(c.get('/api/news-page?limit=100&cursor='+token).status_code,409);self.assertEqual(parent['offset'],before)
 def test_close_owned_bad_scope_token(self):
  b=self.make(200);b.page(P);token=next(iter(self.p.streams.values()))['next']
  with self.p.lock:
   for scope in [5,'','A'*42]:
    with self.assertRaises(ValueError):self.p._close_owned_locked(token,scope)
   scope=next(iter(b.ledger.rows))
   for token2 in ['',5,'A'*42,'?'*43]:
    with self.assertRaises(PageExpired):self.p._close_owned_locked(token2,scope)
  self.assertEqual(b.ledger.total(),1)
 def test_concurrentNewsBusyAndBrokerBusy(self):
  b=self.make();self.p.lock.acquire()
  try:self.assertEqual(b.page(P)[1],429)
  finally:self.p.lock.release()
 def test_one_parent_page_100_publicrows(self):
  b=self.make(1000);a,status=b.page(P);self.assertEqual(status,200);self.assertEqual(len(a['items']),100);self.assertEqual(next(iter(self.p.streams.values()))['offset'],100);self.assertNotIn('NO_PRIVATE_VALUE',str(a))
 def test_quota20_no21_parent_attempt(self):
  b=self.make(3000);a,_=b.page(P)
  for _ in range(19):a,status=self.next(a);self.assertEqual(status,200)
  self.assertEqual(b.calls,20);offset=next(iter(self.p.streams.values()))['offset'];self.assertEqual(self.next(a)[1],429);self.assertEqual(next(iter(self.p.streams.values()))['offset'],offset)
 def test_internal_own_busy_fault_closes_not_retry(self):
  from integration.news_pages import PageBusy
  b=self.make()
  with patch.object(self.p,'_page_locked',side_effect=PageBusy):self.assertEqual(b.page(P)[1],503)
  self.assertEqual(b.ledger.total(),0)
 def test_target_mismatch410_doesnot_advance(self):
  b=self.make(200);a,_=b.page(P);offset=next(iter(self.p.streams.values()))['offset']
  self.assertEqual(self.next(a,params=dict(P,edition='wrong'))[1],410);self.assertEqual(self.p.streams,{});self.assertEqual(b.ledger.total(),0)
 def test_reservation_firstEOF_counts_againstNews16(self):
  from integration.news_pages import PageBusy
  b=self.make(200);self.store.rows=rows(1)
  for _ in range(4):b.page(P)
  self.store.rows=rows(200)
  for _ in range(12):self.p.page(F)
  self.assertEqual(len(self.p.streams),12);self.assertEqual(b.ledger.total(),16)
  with self.assertRaises(PageBusy):self.p.page(F)
 def test_unfinished_retry_rotating_last_next_noadvance(self):
  b=self.make(400);a,_=b.page(P);token=a['next_cursor'];r,_=self.next(a);offset=next(iter(self.p.streams.values()))['offset'];calls=b.calls
  replay,_=self.next(a);self.assertEqual(r,replay);self.assertEqual(next(iter(self.p.streams.values()))['offset'],offset);self.assertEqual(b.calls,calls);self.assertNotEqual(token,r['next_cursor'])
  z,_=self.next(r);self.assertEqual(self.next(a)[1],410);self.assertEqual(len(z['items']),100)
 def test_resolve_before_actualNews_lock(self):
  b=self.make();seen=[];original=self.m.resolve
  def resolve(*args):seen.append(self.p.lock.locked());return original(*args)
  self.m.resolve=resolve;b.page(P);self.assertEqual(seen,[False])
 def test_drop_hook_releases_owned_reservation(self):
  b=self.make(200);a,_=b.page(P);key=next(iter(self.p.streams));self.assertEqual(b.ledger.total(),1)
  with self.p.lock:self.p._drop(key)
  self.assertEqual(b.ledger.rows,{});self.assertEqual(b.ledger.total(),0);self.assertEqual(self.next(a)[1],410)
 def test_expire_reason_passed_to_hook(self):
  b=self.make();b.page(P);self.now=120;reasons=[];original=b.ledger.parent_dropped
  def dropped(key,reason):reasons.append(reason);return original(key,reason)
  b.ledger.parent_dropped=dropped
  with self.p.lock:self.p._expire()
  self.assertEqual(reasons,['expired']);self.assertEqual(b.ledger.total(),0)
 def test_reserve_17_refused_no_find(self):
  b=self.make(200)
  for _ in range(16):self.p.page(F)
  calls=len(self.store.calls);self.assertEqual(b.page(P)[1],429);self.assertEqual(len(self.store.calls),calls);self.assertEqual(b.ledger.rows,{})
 def test_can_open_over16_is_false(self):
  b=self.make(200);b.page(P);scope=next(iter(b.ledger.rows));b.ledger.rows[scope]['parent']=None
  for n in range(16):self.p.streams[str(n)]={}
  try:self.assertFalse(b.ledger.can_open(scope))
  finally:
   for n in range(16):self.p.streams.pop(str(n))
 def test_new_scope_quota_drop_no_leak(self):
  b=self.make();b.calls=20;b.minute=0
  self.assertEqual(b.page(P)[1],429);self.assertEqual(b.ledger.rows,{});self.assertEqual(b.ledger.total(),0);self.assertEqual(self.store.calls,[])
 def test_reply_cache_pruned_after_cleaner_expiry(self):
  b=self.make(200);b.page(P);self.assertEqual(len(b.replies),1);self.now=120
  with self.p.lock:self.p._expire()
  b.page(dict(P,code='9999')) # unknown resolves before lock; no cleanup yet
  self.assertEqual(len(b.replies),1)
  b.page(P);self.assertEqual(len(b.replies),1) # old pruned, one new
  self.assertEqual(set(b.replies),set(b.ledger.rows))
