import unittest,copy
from unittest.mock import patch
from werkzeug.test import Client as HTTPClient
from werkzeug.wrappers import Response
from integration.replay199_composition import build_archive_composition
from integration.collector197_config import CollectorConfig
from integration.replay199_collector import run_archive_cycle
from integration.geo_article_writer import GeoArticleWriter
from integration.finder198_transport import FixedProxyTransport
from tests import test_replay199cb as collector_fixture
from tests.test_replay199cb import proof
from tests import test_replay199ca as broker_fixture
class Tests(unittest.TestCase):
 def setUp(self):
  self.c=collector_fixture.Tests();self.c.setUp();self.b=broker_fixture.Tests();self.b.setUp();self.secret='s'*48;self.proofs=0
  def job():self.proofs+=1;return proof()
  from tests.test_finder198a import O,evidence
  self.O=O;self.values=dict(enabled=True,ledger=self.c.ledger,checkpoints=self.c.cp,status_secret=self.secret,job_evidence=job,clock=lambda:100,service=self.b.s,origin=O,client_identity=lambda r:'trusted',worker_evidence=evidence,budget=self.b.b,transport=self.b.t)
  self.public=lambda e,s:Response('PUBLIC')(e,s);self.app=build_archive_composition(self.public,**self.values);self.h=HTTPClient(self.app,Response);self.csrf=self.b.login(self.h,'alice')
 def status(self,key,**kw):return self.h.get('/api/collect/status/'+key,headers=kw.pop('headers',{'Authorization':'Bearer '+self.secret}),base_url=self.O,**kw)
 def completed(self):
  with patch.object(GeoArticleWriter,'write',return_value={'state':'inserted','attempted':1,'inserted_count':1,'duplicate_count':0,'failed_count':0,'uncertain_count':0,'retry_safe':False}):out=self.c.cycle(writer=self.c.writer)
  self.c.db.data['collector_checkpoints197']=copy.deepcopy(self.c.pc.rows);self.c.core.rollover(expected_revision=self.c.db.data[self.c.db.sn][self.c.db.identity]['revision'],checkpoints=self.c.db.cp);return out['job']
 def test_off_no_collaborators_samepublic(self):
  self.assertIs(build_archive_composition(self.public),self.public)
  with self.assertRaises(ValueError):build_archive_composition(self.public,enabled=1)
 def test_owner_status_archived_coverage_no_fetch_or_write(self):
  key=self.completed();before=copy.deepcopy(self.c.db.data);r=self.status(key);self.assertEqual(r.status_code,200);self.assertTrue(r.json['archived']);self.assertIn('coverage',r.json);self.assertEqual(self.c.db.data,before);self.assertEqual(self.c.calls,1);self.assertEqual(self.proofs,1);self.assertEqual(r.headers['Cache-Control'],'no-store')
 def test_auth_origin_query_body_method_key_before_state(self):
  key='a'*64
  for headers in ({},{'Authorization':'Bearer '+'x'*48},{'Authorization':'Bearer '+self.secret,'Origin':self.O}):self.assertIn(self.status(key,headers=headers).status_code,(401,400))
  self.assertEqual(self.status(key+'?x=1').status_code,400);self.assertEqual(self.status(key,data=b'x').status_code,400);self.assertEqual(self.status('bad').status_code,404)
  self.assertEqual(self.h.post('/api/collect/status/'+key,headers={'Authorization':'Bearer '+self.secret}).status_code,404)
  self.assertEqual(self.h.post('/api/collect',headers={'Authorization':'Bearer '+self.secret}).status_code,404);self.assertEqual(self.c.db.starts,0);self.assertEqual(self.proofs,0)
 def test_corrupt_archive_missing_checkpoint_generic_hold(self):
  key=self.completed();self.c.pc.rows.clear();r=self.status(key);self.assertEqual(r.status_code,503);self.assertEqual(r.json,{'error':'status_unavailable'});self.assertEqual(self.c.calls,1)
  del self.c.db.data[self.c.db.an]['batch:1'];self.assertEqual(self.status(key).status_code,503)
 def test_stale_jobproof_before_archive_reads(self):
  self.values['job_evidence']=lambda:proof(0);h=HTTPClient(build_archive_composition(self.public,**self.values),Response);self.assertEqual(h.get('/api/collect/status/'+'a'*64,headers={'Authorization':'Bearer '+self.secret}).status_code,503);self.assertEqual(self.c.db.starts,0)
 def test_public_and_broker_sameclosed_routes_and_replay(self):
  self.assertEqual(self.h.get('/workspace').data,b'PUBLIC');self.assertEqual(self.h.get('/health').data,b'PUBLIC')
  headers={'Origin':self.O,'X-CSRF-Token':self.csrf}
  with patch.object(FixedProxyTransport,'execute',return_value={'status':200,'body':b'{}'})as call:
   self.assertEqual(self.h.post('/api/finder-broker/ships',base_url=self.O,json={'nonce':'n'*24,'port':'ALL'},headers=headers).status_code,200);self.b.core.rollover(expected_revision=3)
   r=self.h.post('/api/finder-broker/ships',base_url=self.O,json={'nonce':'n'*24,'port':'ALL'},headers=headers);self.assertEqual(r.status_code,409);self.assertEqual(set(r.json),{'ok','state','phase','status','response_bytes','cached_answer'});self.assertEqual(call.call_count,1)
 def test_bothfamily_chain_corruption_before_externalio(self):
  key=self.completed();del self.c.db.data[self.c.db.an]['batch:1'];self.assertEqual(self.status(key).status_code,503)
  self.b.db.provision(1);self.b.core.rollover(expected_revision=0);del self.b.db.data[self.b.db.an]['batch:1']
  with patch.object(FixedProxyTransport,'execute',side_effect=AssertionError)as call:self.assertEqual(self.h.post('/api/finder-broker/ships',base_url=self.O,json={'nonce':'z'*24,'port':'ALL'},headers={'Origin':self.O,'X-CSRF-Token':self.csrf}).status_code,409);self.assertEqual(call.call_count,0)
 def test_old_selected_source_no_wiring(self):
  from pathlib import Path
  r=Path(__file__).resolve().parents[1]
  for p in ('production_entry.py','public_live107.py','integration/collector197_job.py'):self.assertNotIn('replay199',(r/p).read_text())
