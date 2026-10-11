"""Pure E0 planning fixture. Not registered in app, no IO or activation."""
import re
from urllib.parse import urlencode
REGISTRY={
 'workspace':('/workspace',{}),
 'countries':('/workspace/countries',{}),
 'map':('/workspace/map',{}),
 'code':('/workspace/finder/offline.html',{'system':r'[A-Z]{2,3}','edition':r'[A-Za-z0-9:_.-]{1,100}','code':r'[0-9]{2,12}'}),
 'code_news':('/api/code-news-context',{'system':r'[A-Z]{2,3}','edition':r'[A-Za-z0-9:_.-]{1,100}','code':r'[0-9]{2,12}'}),
 # Proposed news-context contract, not existing router implementation.
 'news_context':('/workspace/news-context',{'capability':r'[A-Za-z0-9_-]{43}'}),
}
# Source SYS entries 0 and 1; others refused in this small planning fixture.
SYSTEM_INDEX={'HS':0,'IN':1}
class Refused(ValueError):pass

def link(node,params,*,method='GET',now=0,expires_at=None,verified_identity=False):
 if method!='GET' or type(node)is not str or node not in REGISTRY:raise Refused('Registry GET navigation required')
 if type(params)is not dict or any(type(k)is not str or type(v)is not str for k,v in params.items()):raise Refused('Plain fields required')
 path,schema=REGISTRY[node]
 if not path.startswith('/')or path.startswith('//')or '?'in path or '#'in path:raise Refused('Internal registry path required')
 if set(params)!=set(schema):raise Refused('Exact link fields required')
 for k,v in params.items():
  if len(v)>100 or not re.fullmatch(schema[k],v):raise Refused('Bounded typed field required')
 if node=='news_context':
  if type(now)not in(int,float)or type(expires_at)not in(int,float)or expires_at<=now:
   return {'state':'expired','url':None,'message':'Refresh news to open this context'}
 if node in ('code','code_news')and not verified_identity:raise Refused('Verified catalogue identity required')
 query=urlencode(sorted(params.items()))
 if len(query.encode())>512:raise Refused('Link query byte cap')
 if node=='code':
  if params['system']not in SYSTEM_INDEX:raise Refused('Reviewed system mapping required')
  result=path+'#code='+str(SYSTEM_INDEX[params['system']])+':'+params['code']
 elif node=='code_news':
  # Existing API uses query/system/edition, NOT code. No generic q fallback.
  result=path+'?'+urlencode(sorted({'query':params['code'],'system':params['system'],'edition':params['edition']}.items()))
 else:result=path+('?' + query if query else '')
 return {'state':'ready','url':result,'node':node}

def view(node,params,*,available=False,**kwargs):
 out=link(node,params,**kwargs)
 if out['state']!='ready':return out
 if not available:return {'state':'unavailable','url':None,'message':'This feature is unavailable. Your current context is unchanged.'}
 return out
