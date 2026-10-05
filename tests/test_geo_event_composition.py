"""Fake collections only; no live source access or new source authorization."""
import unittest,time
from datetime import datetime,timezone,timedelta
from unittest.mock import patch
from integration.geo_only_runtime import compose_geo_only
from integration.preview_launcher import build_preview
from tests.test_geo_only_runtime import env,Client,Store
class Index:
 def for_article(self,a):return []
class Cursor:
 def __init__(self,rows,fail=False):self.rows=rows;self.calls=[];self.closed=False;self.fail=fail
 def sort(self,*a):self.calls.append(('sort',a));return self
 def limit(self,*a):self.calls.append(('limit',a));return self
 def max_time_ms(self,*a):self.calls.append(('max_time_ms',a));return self
 def __iter__(self):
  if self.fail:raise RuntimeError('secret-event-uri')
  return iter(self.rows)
 def close(self):self.closed=True
class Events:
 def __init__(self,fail=False):self.calls=[];self.cursors=[];self.fail=fail
 def find(self,q,p):
  self.calls.append((q,p));today=datetime.now(timezone.utc).date().isoformat()
  c=Cursor([{'name':'Fixture conference','event_date':today,'source_url':'https://example.com/event','category':'CONFERENCE','confidence':'HIGH','description':'Fixture only'}],self.fail);self.cursors.append(c);return c
class EventClient(Client):
 def __init__(self,fail=False):super().__init__();self.events=Events(fail)
 def __getitem__(self,key):
  self.paths.append(key)
  if key=='events':return self.events
  return self.store if key=='articles' else self
class Tests(unittest.TestCase):
 def settings(self):
  e=env();e.update(NEWS_EVENTS_READ_ENABLED='true',NEWS_EVENTS_MAPPING_VERIFIED='true',GEO_EVENTS_ALLOWED_HOSTS='example.com');return e
 def app(self,e,client):
  # Composition tests do not need original Finder bytes; synthetic context
  # seam is explicitly not Finder source/parity proof.
  with patch('integration.geo_only_runtime.load_bundled_index',return_value=Index()):return compose_geo_only(e,lambda *a,**k:client)
 def auth(self,app):
  c=app.test_client()
  with c.session_transaction(base_url='https://preview.example') as s:s['preview_authenticated']=True;s['preview_issued_at']=time.time()
  return c
 def test_default_events_off_no_mapping(self):
  c=EventClient();a=self.app(env(),c);self.assertNotIn('events',c.paths);self.assertFalse(a.extensions['geo_events_read_enabled'])
 def test_gates_before_client(self):
  for key,value in [('NEWS_EVENTS_MAPPING_VERIFIED','false'),('NEWS_READ_ENABLED','false'),('PREVIEW_ACCESS_ENABLED','false'),('GEO_EVENTS_COLLECTION','other'),('GEO_DATABASE','other'),('GEO_EVENTS_ALLOWED_HOSTS',''),('GEO_EVENTS_ALLOWED_HOSTS','example.com, example.org'),('NEWS_EVENTS_READ_ENABLED','TRUE')]:
   e=self.settings();e[key]=value;calls=[]
   with patch('integration.geo_only_runtime.load_bundled_index',return_value=Index()):
    with self.assertRaises(ValueError):compose_geo_only(e,lambda *a,**k:calls.append(1))
   self.assertEqual(calls,[])
 def test_original_digest_event_block_and_query_close(self):
  raw=EventClient();a=self.app(self.settings(),raw);c=self.auth(a)
  self.assertEqual(a.test_client().get('/digest-data',base_url='https://preview.example').status_code,403)
  response=c.get('/digest-data',base_url='https://preview.example');self.assertEqual(response.status_code,200)
  data=response.json;self.assertEqual(data['events'],'supplied_snapshot');self.assertEqual(data['event_snapshot']['shown'],1);self.assertIn('Fixture conference',data['html']);self.assertFalse(data['writes']);self.assertFalse(data['delivery'])
  today=datetime.now(timezone.utc).date();q,p=raw.events.calls[0];self.assertEqual(q,{'event_date':{'$gte':today.isoformat(),'$lte':(today+timedelta(days=90)).isoformat()}});self.assertEqual(p['_id'],0)
  cursor=raw.events.cursors[0];self.assertTrue(cursor.closed);self.assertEqual(cursor.calls,[('sort',('event_date',1)),('limit',(1001,)),('max_time_ms',(2000,))])
 def test_event_failure_unavailable_articles_still_work(self):
  raw=EventClient(True);c=self.auth(self.app(self.settings(),raw));r=c.get('/digest-data',base_url='https://preview.example');self.assertEqual(r.status_code,200)
  self.assertEqual(r.json['events'],'unavailable');self.assertEqual(r.json['event_snapshot']['shown'],0);self.assertNotIn('secret-event-uri',r.get_data(as_text=True));self.assertTrue(raw.events.cursors[0].closed)
  self.assertEqual(c.get('/api/news',base_url='https://preview.example').status_code,200)
