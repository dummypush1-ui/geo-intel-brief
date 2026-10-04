import unittest
from datetime import datetime,timezone
from integration.event_reader import ReadOnlyEventsReader,EventReadUnavailable,FIELDS
from integration.dashboard_snapshots import DashboardSnapshots
NOW=datetime(2026,10,5,tzinfo=timezone.utc)
def row(day='2026-10-05',**kw):return dict(name='Trade meeting',event_date=day,source_url='https://www.wto.org/event',category='TRADE',confidence='announced',description='fixture only',**kw)
class Cursor:
 def __init__(self,rows,log):self.rows=rows;self.log=log
 def sort(self,*a):self.log.append(('sort',a));return self
 def limit(self,n):self.log.append(('limit',n));self.n=n;return self
 def max_time_ms(self,n):self.log.append(('deadline',n));return self
 def close(self):self.log.append(('close',True))
 def __iter__(self):return iter(self.rows[:self.n])
class Store:
 def __init__(self,rows):self.rows=rows;self.log=[]
 def find(self,*a):self.log.append(('find',a));return Cursor(self.rows,self.log)
class EventReaderTests(unittest.TestCase):
 def reader(self,rows,**kw):self.store=Store(rows);return ReadOnlyEventsReader(self.store,lambda:NOW,verified=True,**kw)
 def test_original_inclusive_query_projection_and_bounds(self):
  reader=self.reader([row(),row('2027-01-03')]);r=reader();self.assertEqual(len(r['items']),2)
  self.assertEqual(self.store.log[0][1][0],{'event_date':{'$gte':'2026-10-05','$lte':'2027-01-03'}})
  self.assertEqual(self.store.log[0][1][1],dict({k:1 for k in FIELDS},_id=0));self.assertIn(('sort',('event_date',1)),self.store.log);self.assertIn(('deadline',2000),self.store.log)
 def test_empty_vs_unavailable_and_host_policy(self):
  r=self.reader([]);snap=DashboardSnapshots({'geo_events':r},verified=True,allowed_hosts={'geo_events':['www.wto.org']});self.assertEqual(snap('geo')['panels']['geo_events']['state'],'supplied_snapshot')
  r=self.reader([row('2026-10-04')]);snap=DashboardSnapshots({'geo_events':r},verified=True,allowed_hosts={'geo_events':['www.wto.org']});self.assertEqual(snap('geo')['panels']['geo_events']['state'],'unavailable')
 def test_no_private_fields_and_mutation(self):
  r=self.reader([row(_id='SECRET',token='SECRET')])();self.assertNotIn('SECRET',str(r));self.assertEqual(set(r['items'][0]),set(FIELDS))
 def test_bad_date_order_budget_surrogate_and_overflow(self):
  for rows,kw in [([row('2026-10-06'),row()],{}),([row('bad')],{}),([{**row(),'description':'x'*2000}],{'max_bytes':1024}),([{**row(),'name':'bad\ud800'}],{}),([row(),row()],{'limit':1})]:
   with self.assertRaises(EventReadUnavailable):self.reader(rows,**kw)()
   self.assertIn(('close',True),self.store.log)
 def test_fixed_timezone_and_missing_review_refused(self):
  with self.assertRaises(ValueError):ReadOnlyEventsReader(Store([]),lambda:NOW)
  with self.assertRaises(EventReadUnavailable):ReadOnlyEventsReader(Store([]),lambda:datetime(2026,10,5),verified=True)()

 def test_setup_failures_always_close_original_cursor(self):
  for failure in ('sort','limit','max_time_ms'):
   log=[]
   class BrokenCursor:
    def sort(self,*a):
     if failure=='sort':raise RuntimeError('fixture')
     return self
    def limit(self,*a):
     if failure=='limit':raise RuntimeError('fixture')
     return self
    def max_time_ms(self,*a):raise RuntimeError('fixture')
    def close(self):log.append('closed')
   store=type('Store',(),{'find':lambda s,*a:BrokenCursor()})()
   with self.assertRaises(EventReadUnavailable):ReadOnlyEventsReader(store,lambda:NOW,verified=True)()
   self.assertEqual(log,['closed'],failure)
 def test_complete_envelope_budget(self):
  import json
  item=row();item['description']='x'*(1024-len(json.dumps({**item,'description':''},ensure_ascii=False,separators=(',',':')).encode()))
  self.assertEqual(len(json.dumps(item,ensure_ascii=False,separators=(',',':')).encode()),1024)
  with self.assertRaises(EventReadUnavailable):self.reader([item],max_bytes=1024)()
