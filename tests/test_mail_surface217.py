import ast,copy,hashlib,io,json,re,subprocess,unittest
from pathlib import Path
from integration.mail_surface217 import build_mail_surface,metadata,HELD
ROOT=Path(__file__).parents[1]
SECRET='SECRET_CANARY_'+'s'*48
CONFIG={'origin':'https://fixture.invalid','rail':'apps_script','channel_id':'a'*64,'header_secret':SECRET}
class Trap:
 def __getattribute__(self,k):raise AssertionError('CANARY_ACCESS')
class Stream:
 def __init__(self,raw):self.raw=raw;self.reads=[]
 def read(self,n):self.reads.append(n);return self.raw[:n]
class Tests(unittest.TestCase):
 def env(self,path='/internal/mail/v1/prepare',body=None,**kw):
  raw=json.dumps(body or {'kind':'digest','nonce':'n'*20}).encode()
  return {'PATH_INFO':path,'SCRIPT_NAME':'/mounted','REQUEST_METHOD':'POST','HTTP_AUTHORIZATION':'Bearer '+SECRET,'QUERY_STRING':'','wsgi.url_scheme':'https','HTTP_HOST':'fixture.invalid','CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(raw)),'wsgi.input':Stream(raw),**kw}
 def call(self,e,app=None):
  saved=[];a=app or build_mail_surface(lambda e,s:[],enabled=True,config=CONFIG)
  out=a(e,lambda s,h:saved.append((s,h)));return saved[0],b''.join(out)
 def test_off_identity_hostile(self):
  p=Trap();self.assertIs(build_mail_surface(p,config=Trap()),p);self.assertIs(build_mail_surface(p,enabled=False,config=Trap()),p)
  for v in (1,None,'true'):
   with self.assertRaises(ValueError):build_mail_surface(p,enabled=v,config=Trap())
 def test_held_all_operations_and_no_leak(self):
  for kind in ('digest','critical','weekly'):
   s,b=self.call(self.env(body={'kind':kind,'nonce':'n'*20}));self.assertEqual(s[0],'503 Service Unavailable');self.assertEqual(json.loads(b),{'state':'mail_integration_held','retry_send':False})
  for action in ('claim','ack'):
   s,b=self.call(self.env('/internal/mail/v1/'+action,{'receipt':'b'*64,'hash':'c'*64,'attempt':'n'*20}));self.assertEqual(s[0],HELD[0]);self.assertNotIn(SECRET,b.decode())
  s,b=self.call(self.env('/internal/mail/v1/receipts/'+'b'*64,REQUEST_METHOD='GET',CONTENT_LENGTH='0'))
  self.assertEqual(s[0],HELD[0]);self.assertEqual(dict(s[1])['Cache-Control'],'no-store');self.assertNotIn('Retry-After',dict(s[1]))
 def test_uniform_auth_no_body_or_method_access(self):
  baseline=self.call(self.env('/internal/mail/v1/unknown',HTTP_AUTHORIZATION='bad',**{'wsgi.input':Trap()}))
  for auth in (None,'', 'Bearer wrong', 'Bearer\t'+SECRET,'Bearer  '+SECRET,'Bearer '+SECRET+', Bearer '+SECRET,'Bearer '+SECRET+'é'):
   e=self.env(HTTP_AUTHORIZATION=auth,**{'wsgi.input':Trap()},CONTENT_LENGTH=Trap(),HTTP_TRANSFER_ENCODING=Trap(),REQUEST_METHOD=Trap())
   self.assertEqual(self.call(e),baseline)
  self.assertEqual(self.call(self.env(QUERY_STRING='x',**{'wsgi.input':Trap()})),baseline)
 def test_suspicious_routes_uniform(self):
  baseline=self.call(self.env(HTTP_AUTHORIZATION='bad'))
  for p in ['/internal/mail/v1x','//internal/mail/v1','/internal/mail/v1/..','/internal/mail/./v1','/internal/mail/%76%31','/internal/mail/v1%2fprepare','/internal/mail/v1%2Fprepare','/internal/mail/v1%5cprepare','/internal/mail/%2e/v1','/internal/mail/v1\\prepare','/internal/mail/v1\0','/INTERNAL/MAIL/V1','/internal/mail/v1.']:
   self.assertEqual(self.call(self.env(p,**{'wsgi.input':Trap()})),baseline,p)
 def test_passthrough_same_environment_and_exception(self):
  e=self.env('/workspace',SCRIPT_NAME='/internal/mail/v1');before=dict(e);got=[]
  def public(x,s):got.append(x);s('201 Created',[]);return [b'PUBLIC']
  out=self.call(e,build_mail_surface(public,enabled=True,config=CONFIG));self.assertEqual(out,(('201 Created',[]),b'PUBLIC'));self.assertIs(got[0],e);self.assertEqual(e,before)
  err=RuntimeError('PUBLIC_CANARY')
  def fail(e,s):raise err
  with self.assertRaises(RuntimeError)as c:self.call(e,build_mail_surface(fail,enabled=True,config=CONFIG))
  self.assertIs(c.exception,err)
 def test_methods_and_paths(self):
  for m in ('HEAD','OPTIONS','PUT','DELETE','PATCH','GET'):
   self.assertEqual(self.call(self.env(REQUEST_METHOD=m))[0][0],'405 Method Not Allowed')
  for path in ('','/unknown','/receipts/'+'b'*65):
   self.assertEqual(self.call(self.env('/internal/mail/v1'+path))[0][0],'404 Not Found')
 def test_strict_body_caps_framing_and_schema(self):
  raws=[b'{}',b'[]',b'\xef\xbb\xbf{}',b'\xff',b'{"kind":"digest","kind":"critical","nonce":"'+b'n'*20+b'"}',b'{"kind":NaN,"nonce":"'+b'n'*20+b'"}',b'{"kind":Infinity,"nonce":"'+b'n'*20+b'"}',b'{"kind":true,"nonce":"'+b'n'*20+b'"}',b'{"kind":"digest","nonce":"short"}',b'X'*4097]
  for raw in raws:
   e=self.env(CONTENT_LENGTH=str(len(raw)),**{'wsgi.input':Stream(raw),'wsgi.input_terminated':True});self.assertEqual(self.call(e)[0][0],'400 Bad Request');self.assertTrue(all(n<=4097 for n in e['wsgi.input'].reads))
  for update in ({'CONTENT_LENGTH':''},{'CONTENT_LENGTH':None},{'CONTENT_LENGTH':'001'},{'CONTENT_LENGTH':'4097'},{'HTTP_TRANSFER_ENCODING':'chunked'},{'CONTENT_TYPE':'text/json'},{'CONTENT_LENGTH':'2'}):
   self.assertEqual(self.call(self.env(**update))[0][0],'400 Bad Request')
  raw=b'{}'+b'x'*5000;e=self.env(CONTENT_LENGTH='2',**{'wsgi.input':Stream(raw),'wsgi.input_terminated':True});self.assertEqual(self.call(e)[0][0],'400 Bad Request');self.assertEqual(e['wsgi.input'].reads,[4097])
 def test_config_fixed_secret_only_digest(self):
  app=build_mail_surface(lambda e,s:[],enabled=True,config=CONFIG);self.assertNotIn(SECRET,repr(app));self.assertEqual(app._credential_digest,hashlib.sha256(('Bearer '+SECRET).encode()).digest());self.assertNotIn(SECRET,str(app.__dict__))
  bad=[{**CONFIG,'x':1},{**CONFIG,'rail':'smtp'},{**CONFIG,'header_secret':' '+SECRET},{**CONFIG,'channel_id':'A'*64}]
  for origin in ('http://fixture.invalid','https://fixture.invalid/','https://fixture.invalid:443','https://u@fixture.invalid','https://FIXTURE.invalid','https://127.0.0.1','https://localhost','https://[::1]','https://fixture.invalid?x'):
   bad.append({**CONFIG,'origin':origin})
  class D(dict):pass
  bad.append(D(CONFIG))
  for config in bad:
   with self.assertRaises(ValueError)as c:build_mail_surface(lambda e,s:[],enabled=True,config=config)
   self.assertNotIn(SECRET,str(c.exception));self.assertIsNone(c.exception.__cause__);self.assertIsNone(c.exception.__context__)
 def test_internal_failure_no_state_next_request(self):
  app=build_mail_surface(lambda e,s:[],enabled=True,config=CONFIG)
  e=self.env(**{'wsgi.input':Trap()});s,b=self.call(e,app);self.assertNotIn('CANARY',b.decode());self.assertEqual(s[0],'400 Bad Request');self.assertEqual(self.call(self.env(),app)[0][0],HELD[0])
 def test_metadata_ast_import_edge(self):
  self.assertEqual(metadata(),{'state':'mounted_held','wired':False,'live':False,'ready':False,'rail':'apps_script','smtp_fallback_held':True})
  p=ROOT/'integration/mail_surface217.py';tree=ast.parse(p.read_text());imports=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Import):imports.extend(a.name for a in n.names)
   if isinstance(n,ast.ImportFrom):imports.append(n.module)
  self.assertEqual(set(imports),{'hashlib','hmac','json','re','urllib.parse'})
  for path in [ROOT/'production_entry.py',ROOT/'public_live107.py',ROOT/'integration/public_live_builder.py']:
   self.assertNotIn('mail_surface217',path.read_text())
 def test_bridge_held_mock(self):
  r=subprocess.run(['node','feature_mail_mount/test_surface217.js'],cwd=ROOT,capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
