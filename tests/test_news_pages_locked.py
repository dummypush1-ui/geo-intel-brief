import unittest,time
from unittest.mock import patch
from integration.news_pages import WholeGeoPages,PageBusy,PageExpired
from integration.news_api import create_app
from integration.public_live_builder import sanitize_public_geo_rows
from tests.test_news_pages185 import Store,rows,F
class LockedTests(unittest.TestCase):
 def setUp(self):self.now=0;self.store=Store(rows(100));self.p=WholeGeoPages(self.store,sanitize_public_geo_rows,verified=True,clock=lambda:self.now,start_cleaner=False);self.addCleanup(self.p.close);self.scope='D'*43
 def test_wrapper_delegates_internal_once_None(self):
  with patch.object(self.p,'_page_locked',return_value={'fixture':1})as internal:
   self.assertEqual(self.p.page(F,25,''),{'fixture':1});internal.assert_called_once_with(F,25,'',owner_scope=None)
  self.assertTrue(self.p.lock.acquire(False));self.p.lock.release()
 def test_internal_requires_held_lock_recursive_public_busy(self):
  with self.assertRaises(RuntimeError):self.p._page_locked(F)
  with self.p.lock:
   start=time.monotonic()
   with self.assertRaises(PageBusy):self.p.page(F)
   self.assertLess(time.monotonic()-start,.05)
   r=self.p._page_locked(F,owner_scope=self.scope);self.assertEqual(len(r['items']),25)
 def test_scope_mismatch_bothways_no_touch_advance(self):
  a=self.p.page(F);news=a['next_cursor']
  with self.p.lock:d=self.p._page_locked(F,owner_scope=self.scope)
  token=d['next_cursor'];offsets={k:s['offset']for k,s in self.p.streams.items()};self.now=10
  with self.p.lock:
   for t,scope in [(news,self.scope),(token,None),(token,'X'*43)]:
    with self.assertRaises(PageExpired):self.p._page_locked(F,25,t,owner_scope=scope)
  self.assertEqual(offsets,{k:s['offset']for k,s in self.p.streams.items()});self.assertTrue(all(s['used']==0 for s in self.p.streams.values()))
 def test_news_endpoint_cannot_advance_D_409(self):
  with self.p.lock:d=self.p._page_locked(F,owner_scope=self.scope)
  c=create_app(full_news_pages=self.p,authorize=lambda _:True).test_client();r=c.get('/api/news-page?cursor='+d['next_cursor'])
  self.assertEqual(r.status_code,409);self.assertEqual(next(iter(self.p.streams.values()))['offset'],25)
 def test_owned_close_one_not_ALL(self):
  news=self.p.page(F)
  with self.p.lock:
   d=self.p._page_locked(F,owner_scope=self.scope)
   with self.assertRaises(PageExpired):self.p._close_owned_locked(news['next_cursor'],self.scope)
   with self.assertRaises(PageExpired):self.p._close_owned_locked(d['next_cursor'],'X'*43)
   self.p._close_owned_locked(d['next_cursor'],self.scope)
  self.assertEqual(len(self.p.streams),1);self.assertEqual(self.store.cursors[0].closed,0);self.assertEqual(self.store.cursors[1].closed,1)
  self.assertEqual(len(self.p.page(F,25,news['next_cursor'])['items']),25)
 def test_exact16_and_17(self):
  for _ in range(16):self.p.page(F)
  self.assertEqual(len(self.store.calls),16)
  with self.assertRaises(PageBusy):self.p.page(F)
  self.assertEqual(len(self.store.calls),16)
 def test_exact120_idle(self):
  a=self.p.page(F);self.now=119
  with self.p.lock:self.p._expire()
  self.assertEqual(len(self.p.streams),1);self.now=120
  with self.p.lock:self.p._expire()
  self.assertEqual(len(self.p.streams),0);self.assertEqual(self.store.cursors[0].closed,1)
  with self.assertRaises(PageExpired):self.p.page(F,25,a['next_cursor'])
 def test_exact1800_born_frequent_replay(self):
  a=self.p.page(F);b=self.p.page(F,25,a['next_cursor']);t=a['next_cursor']
  for now in range(100,1800,100):self.now=now;self.assertEqual(self.p.page(F,25,t),b)
  self.now=1800
  with self.assertRaises(PageExpired):self.p.page(F,25,t)
  self.assertEqual(len(self.p.streams),0)
 def test_first_EOF_drop_replay_EOF_kept(self):
  p=WholeGeoPages(Store(rows(1)),sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(p.close);self.assertTrue(p.page(F)['exhausted']);self.assertEqual(p.streams,{})
  p2=WholeGeoPages(Store(rows(30)),sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(p2.close);a=p2.page(F);t=a['next_cursor'];b=p2.page(F,25,t);self.assertTrue(b['exhausted']);self.assertEqual(len(p2.streams),1);self.assertEqual(p2.page(F,25,t),b)
 def test_validation_before_lock_wrapper_exception_releases(self):
  with self.p.lock:
   with self.assertRaises(ValueError):self.p.page(F,101)
  with patch.object(self.p,'_page_locked',side_effect=PageExpired):
   with self.assertRaises(PageExpired):self.p.page(F)
  self.assertTrue(self.p.lock.acquire(False));self.p.lock.release()
class ExplicitLockBoundaries(unittest.TestCase):
 def setUp(self):self.p=WholeGeoPages(Store(rows(100)),sanitize_public_geo_rows,verified=True,start_cleaner=False);self.addCleanup(self.safe_close)
 def safe_close(self):
  if self.p.lock.locked():self.p.lock.release()
  self.p.close()
 def test_close_owned_requires_lock(self):
  with self.assertRaises(RuntimeError):self.p._close_owned_locked('A'*43,'D'*43)
 def test_page_owned_scope_strict(self):
  with self.p.lock:
   for scope in [5,'','x','A'*42]:
    with self.assertRaises(ValueError):self.p._page_locked(F,owner_scope=scope)
  self.assertEqual(self.p.streams,{})
 def test_exception_explicitly_unlocks(self):
  with patch.object(self.p,'_page_locked',side_effect=PageExpired):
   with self.assertRaises(PageExpired):self.p.page(F)
  self.assertFalse(self.p.lock.locked(),'page wrapper failed to release after exception')
 def test_second_caller_busy_fast_without_hang(self):
  from threading import Thread,Event
  finished=Event();out=[];self.p.lock.acquire()
  def caller():
   try:self.p.page(F);out.append('advanced')
   except PageBusy:out.append('busy')
   except Exception as e:out.append(type(e).__name__)
   finally:finished.set()
  t=Thread(target=caller,daemon=True);t.start()
  fast=finished.wait(.1)
  self.p.lock.release();t.join(1)
  self.assertTrue(fast,'second caller blocked instead of returning PageBusy')
  self.assertEqual(out,['busy']);self.assertEqual(self.p.store.calls,[])
