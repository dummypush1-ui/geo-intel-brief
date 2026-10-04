"""Fresh-process proof: traps installed before target's first import/request."""
import builtins,json,os,sys,socket,smtplib,requests,dotenv
from unittest.mock import patch
from contextlib import ExitStack
from datetime import datetime,timezone
# Framework initialization may use environment; target import remains cold.
import flask,zoneinfo
zoneinfo.ZoneInfo("UTC")
assert not any(k.startswith('integration.') or k.startswith('intelligence.') for k in sys.modules)
def trap(*args,**kwargs):raise AssertionError('Forbidden cold-preview capability')
original_import=builtins.__import__
original_open=builtins.open
class TrappedEnv(dict):
 def get(self,*a,**k):return trap(*a,**k)
 def __getitem__(self,key):return trap(key)
def source_open(file,*args,**kwargs):
 # Import machinery uses loader IO; explicit renderer source uses Path.read_bytes.
 return trap(file)
def no_original_import(name,*args,**kwargs):
 if name.startswith('intelligence'):raise AssertionError('Original import forbidden: '+name)
 return original_import(name,*args,**kwargs)
with ExitStack() as stack:
 for target in ['os.getenv','dotenv.load_dotenv','dotenv.dotenv_values','socket.socket','socket.create_connection','smtplib.SMTP','smtplib.SMTP_SSL','requests.get','requests.post']:
  stack.enter_context(patch(target,trap))
 stack.enter_context(patch('builtins.__import__',no_original_import))
 stack.enter_context(patch('flask.sansio.app.get_debug_flag',lambda:False))
 stack.enter_context(patch('os.environ',TrappedEnv()))
 stack.enter_context(patch('builtins.open',source_open))
 from integration.news_api import create_app
 from integration.renderer_scope import renderer
 row={'_id':'COLD-PRIVATE-ID','article_key':'COLD-PUBLIC-KEY','title':'Cold fixture','url':'https://example.com/a','score':50,'risk_level':'CRITICAL','category':'TRADE','created_at':datetime.now(timezone.utc).isoformat()}
 app=create_app(reader=lambda:{'geo':[row]},authorize=lambda r:True)
 client=app.test_client()
 for path in ['/digest-data','/critical','/weekly']:
  result=client.get(path);assert result.status_code==200,(path,result.text)
  assert 'Cold fixture' in result.json['html'];assert not result.json['writes'];assert 'COLD-PRIVATE-ID' not in result.text;assert 'COLD-PUBLIC-KEY' not in result.text
 fn=renderer('geo_critical',{})
 assert not {'smtplib','ssl','Path','mark_emailed','send','_archive','EMAIL_APP_PASSWORD','__import__'} & set(fn.__globals__)
 assert '__import__' not in fn.__globals__['__builtins__']
 assert not any(k.startswith('intelligence.') for k in sys.modules)
print(json.dumps({'fresh_process':True,'target_import_and_three_first_requests':True,'dotenv_env_network_smtp_traps':True,'environ_get_item_and_builtin_open_traps':True,'original_module_imports':0,'identifier_output':False,'writes':False}))
