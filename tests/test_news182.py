import unittest,importlib,ast
from pathlib import Path
from unittest.mock import patch,MagicMock
from datetime import datetime,timezone
class Tests(unittest.TestCase):
 def test_seed_empty_no_write(self):
  m=importlib.import_module('intelligence.geo.collectors.events')
  with patch.object(m,'save_event',side_effect=AssertionError)as save:self.assertEqual(m.seed_events(),0);save.assert_not_called()
 def test_invalid_events_before_connect(self):
  m=importlib.import_module('intelligence.geo.database')
  with patch.object(m,'connect',side_effect=AssertionError)as connect:
   for row in ({},{'name':' ','event_date':'2026-01-01'},{'name':'a','event_date':'2026-02-30'},{'name':'a','event_date':'20261009'},{'name':'a','event_date':'2026-1-01'},{'name':'a','event_date':None}):
    with self.assertRaises(ValueError):m.save_event(row)
   connect.assert_not_called()
 def test_valid_event_detached(self):
  m=importlib.import_module('intelligence.geo.database');row={'name':'Fixture','event_date':'2026-10-09'};db=MagicMock()
  with patch.object(m,'connect',return_value=db):self.assertTrue(m.save_event(row))
  self.assertNotIn('created_at',row);self.assertIn('created_at',db.events.insert_one.call_args.args[0])
 def test_provider_dates_held_not_now(self):
  path=Path('intelligence/geo/collectors/gnews_search.py');tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='collect');now=datetime(2026,10,9,tzinfo=timezone.utc)
  from integration.publication_dates.policy import publication_date
  rows=[{'title':str(i),'url':'https://fixture.invalid/'+str(i),'published date':v,'publisher':'Fixture'}for i,v in enumerate(['Thu, 08 Oct 2026 12:00:00 GMT',None,'bad','2026-10-08','2026-10-08T12:00:00 XYZ','2026-10-10T00:00:00Z'])]
  captured=[];client=MagicMock();client.get_news.return_value=rows
  scope={'HAS_GNEWS':True,'GNews':lambda **k:client,'GNEWS_LANGUAGE':'en','GNEWS_COUNTRY':'IN','GNEWS_MAX_RESULTS':10,'GNEWS_PERIOD':'1d','_build_queries':lambda:['fixture'],'datetime':type('Clock',(),{'now':staticmethod(lambda tz:now)}),'timezone':timezone,'publication_date':publication_date,'strip_html':lambda x:x,'classify':lambda *a:('TRADE',80,'LOW','IN'),'ACTIVE_CATEGORIES':['TRADE'],'dedupe_articles':lambda x,**k:x,'DEDUPE_THRESHOLD':.85,'save_articles_bulk':lambda docs:captured.extend(docs)or len(docs),'ArticleWriteOutcomeError':RuntimeError}
  exec(compile(ast.Module(body=[fn],type_ignores=[]),'fixture','exec'),scope);self.assertEqual(scope['collect'](),1);self.assertEqual(captured[0]['published'],'2026-10-08T12:00:00+00:00');self.assertEqual(captured[0]['source'],'Fixture')
