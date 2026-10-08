import unittest
from flask import Flask, jsonify
from integration.edge_guard import EdgeGuard, install_edge_guard, client_ip, edge_limits_from_env


class Clock:
 def __init__(self):self.t=1000.0
 def __call__(self):return self.t


def make(**limits):
 clock=Clock()
 app=Flask(__name__)
 @app.before_request
 def deny_all():  # stands in for the app authorize guard (runs after edge guard)
  from flask import request
  if request.path=='/health':return None
  if request.path=='/ok':return None
  return jsonify(error='private'),403
 @app.get('/ok')
 def ok():return jsonify(ok=True)
 @app.get('/health')
 def health():return jsonify(state='staging')
 @app.post('/ok')
 def post():return jsonify(ok=True)
 install_edge_guard(app,EdgeGuard(clock=clock,**limits))
 return app,clock


def ip(n):return {'X-Forwarded-For':'9.9.9.9, 10.0.0.%d'%n}


class EdgeGuardTests(unittest.TestCase):
 def test_normal_requests_pass_unchanged(self):
  app,_=make();c=app.test_client()
  r=c.get('/ok?q=iran&category=trade',headers=ip(1))
  self.assertEqual(r.status_code,200);self.assertEqual(r.get_json(),{'ok':True})
  self.assertEqual(c.get('/other',headers=ip(1)).status_code,403)  # app guard still decides

 def test_rate_limit_per_client_and_window_reset(self):
  app,clock=make(rate_limit=3);c=app.test_client()
  codes=[c.get('/ok',headers=ip(1)).status_code for _ in range(5)]
  self.assertEqual(codes,[200,200,200,429,429])
  r=c.get('/ok',headers=ip(1));self.assertEqual(r.headers['Retry-After'],'60')
  self.assertEqual(c.get('/ok',headers=ip(2)).status_code,200)  # other client unaffected
  clock.t+=61
  self.assertEqual(c.get('/ok',headers=ip(1)).status_code,200)

 def test_health_is_exempt(self):
  app,_=make(rate_limit=1);c=app.test_client()
  for _ in range(5):self.assertEqual(c.get('/health',headers=ip(1)).status_code,200)

 def test_spoofed_left_xff_does_not_evade_limit(self):
  app,_=make(rate_limit=2);c=app.test_client()
  codes=[c.get('/ok',headers={'X-Forwarded-For':'1.1.1.%d, 10.0.0.5'%i}).status_code for i in range(4)]
  self.assertEqual(codes,[200,200,429,429])

 def test_honeypot_bans_only_after_strikes_then_expires(self):
  app,clock=make();c=app.test_client()
  self.assertEqual(c.get('/wp-login.php',headers=ip(1)).status_code,404)
  self.assertEqual(c.get('/.env',headers=ip(1)).status_code,404)
  self.assertEqual(c.get('/ok',headers=ip(1)).status_code,200)   # 2 strikes: a planted <img> alone cannot ban
  self.assertEqual(c.get('/.env',headers=ip(1)).status_code,404)  # 3rd strike
  self.assertEqual(c.get('/ok',headers=ip(1)).status_code,429)
  self.assertEqual(c.get('/ok',headers=ip(2)).status_code,200)
  clock.t+=901
  self.assertEqual(c.get('/ok',headers=ip(1)).status_code,200)

 def test_strikes_expire(self):
  app,clock=make();c=app.test_client()
  for _ in range(2):c.get('/.env',headers=ip(8))
  clock.t+=901
  c.get('/.env',headers=ip(8))
  self.assertEqual(c.get('/ok',headers=ip(8)).status_code,200)

 def test_honeypot_case_and_trailing_slash_and_prefix(self):
  app,_=make();c=app.test_client()
  for p in ('/WP-Login.php','/phpmyadmin/','/cgi-bin/anything'):
   self.assertEqual(c.get(p,headers=ip(3)).status_code,404,p)

 def test_real_routes_are_not_honeypots(self):
  app,_=make();c=app.test_client()
  for p in ('/ok','/health','/workspace','/api/news','/api/country-page'):
   self.assertNotEqual(c.get(p,headers=ip(4)).status_code,404 if p in ('/ok','/health') else 429,p)
  self.assertEqual(c.get('/ok',headers=ip(4)).status_code,200)  # still not banned

 def test_input_validation(self):
  app,_=make(max_args=3,max_value=10,max_query_string=100);c=app.test_client()
  h=ip(5)
  self.assertEqual(c.get('/ok?q='+'a'*11,headers=h).status_code,400)
  self.assertEqual(c.get('/ok?a=1&b=2&c=3&d=4',headers=h).status_code,400)
  self.assertEqual(c.get('/ok?q=%00x',headers=h).status_code,400)
  self.assertEqual(c.get('/ok?q=%ff',headers=h).status_code,400)
  self.assertEqual(c.get('/ok?'+'a=1&'*40,headers=h).status_code,400)
  self.assertEqual(c.get('/ok?q=fine',headers=h).status_code,200)

 def test_body_and_method_limits(self):
  app,_=make(max_body=10);c=app.test_client();h=ip(6)
  self.assertEqual(c.post('/ok',data=b'x'*11,headers=h).status_code,413)
  self.assertEqual(c.post('/ok',data=b'x'*5,headers=h).status_code,200)
  self.assertEqual(c.open('/ok',method='TRACE',headers=h).status_code,400)

 def test_client_tracking_is_bounded(self):
  app,_=make(max_clients=5);c=app.test_client()
  for i in range(50):c.get('/ok',headers={'X-Forwarded-For':'8.8.8.8, 10.1.0.%d'%i})
  g=app._edge_guard
  self.assertLessEqual(len(g._hits),5);self.assertLessEqual(len(g._bans),5)

 def test_install_twice_and_bad_limits_rejected(self):
  app,_=make()
  with self.assertRaises(ValueError):install_edge_guard(app)
  with self.assertRaises(ValueError):EdgeGuard(rate_limit=0)
  with self.assertRaises(ValueError):EdgeGuard(bogus=1)

 def test_guard_runs_before_existing_hooks(self):
  app,_=make();c=app.test_client()
  self.assertEqual(c.get('/wp-login.php',headers=ip(7)).status_code,404)  # not the app's 403


class EnvTests(unittest.TestCase):
 def test_off_unless_exactly_true(self):
  for env in ({},{'EDGE_GUARD_ENABLED':'false'},{'EDGE_GUARD_ENABLED':'1'},{'EDGE_GUARD_ENABLED':'yes'},{'EDGE_GUARD_ENABLED':''}):
   self.assertIsNone(edge_limits_from_env(env),env)
  for v in ('true','TRUE',' True '):self.assertEqual(edge_limits_from_env({'EDGE_GUARD_ENABLED':v}),{})

 def test_rate_limit_parsing(self):
  on={'EDGE_GUARD_ENABLED':'true'}
  self.assertEqual(edge_limits_from_env({**on,'EDGE_RATE_LIMIT':'7'}),{'rate_limit':7})
  for bad in ('\u00b2','\u0663','0','-5','abc','1.5','99999999999'):
   with self.assertLogs('integration.edge_guard',level='WARNING'):
    self.assertEqual(edge_limits_from_env({**on,'EDGE_RATE_LIMIT':bad}),{},bad)


class EntryRunner:
 """Runs the real public entrypoint in a subprocess so sys.modules stays clean.
 Plain mixin (not a TestCase) so importing modules do not re-collect its tests."""
 SCRIPT=r"""
import json,os,sys
from urllib.parse import urlsplit
import public_live107 as m
app=m.app;c=app.test_client();B='https://example.onrender.com'
def h(n):return {'X-Forwarded-For':'1.1.1.1, 10.0.0.%d'%n}
out={'guard':getattr(app,'_edge_guard',None) is not None}
out['health']=c.get('/health',base_url=B).status_code
out['news']=c.get('/api/news',base_url=B,headers=h(1)).status_code
out['hp']=[c.get('/.env',base_url=B,headers=h(2)).status_code for _ in range(3)]
out['after_ban']=c.get('/api/news',base_url=B,headers=h(2)).status_code
out['other_client']=c.get('/api/news',base_url=B,headers=h(3)).status_code
print(json.dumps(out))
"""
 def run_entry(self,extra):
  import json,os,subprocess,sys
  from pathlib import Path
  env={'PATH':os.environ.get('PATH',''),'PYTHONPATH':str(Path(__file__).resolve().parents[1]),'PUBLIC_NEWS_READ_ENABLED':'false','PREVIEW_PUBLIC_SAMPLE_ENABLED':'true','PREVIEW_GEO_ONLY_ENABLED':'true','PREVIEW_ACCESS_ENABLED':'false','NEWS_READ_ENABLED':'false','NEWS_EVENTS_READ_ENABLED':'false','FINDER_NETWORK_PREVIEW_ENABLED':'false','PREVIEW_ORIGIN':'https://example.onrender.com',**extra}
  p=subprocess.run([sys.executable,'-c',self.SCRIPT],capture_output=True,text=True,env=env,cwd=str(Path(__file__).resolve().parents[1]),timeout=60)
  self.assertEqual(p.returncode,0,p.stderr[-800:])
  return json.loads(p.stdout.strip().splitlines()[-1])


class EntrypointWiringTests(EntryRunner,unittest.TestCase):
 def test_default_is_unguarded(self):
  o=self.run_entry({})
  self.assertFalse(o['guard']);self.assertEqual(o['news'],200)
  self.assertEqual(o['hp'],[403,403,403])   # app's own authorize guard, no honeypot
 def test_enabled_guard_wired(self):
  o=self.run_entry({'EDGE_GUARD_ENABLED':'True'})
  self.assertTrue(o['guard']);self.assertEqual(o['health'],200);self.assertEqual(o['news'],200)
  self.assertEqual(o['hp'],[404,404,404]);self.assertEqual(o['after_ban'],429);self.assertEqual(o['other_client'],200)
 def test_bad_rate_limit_does_not_break_boot(self):
  o=self.run_entry({'EDGE_GUARD_ENABLED':'true','EDGE_RATE_LIMIT':'\u00b2'})
  self.assertTrue(o['guard'])


if __name__=='__main__':unittest.main()
