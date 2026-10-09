"""Closed 198b-a connector CONTRACT. Disabled catalog, no default live adapter.
Plans only reviewed fixed routes; does not inherit upstream rotation/quota/CORS.
One proxy request may trigger unknown upstream attempts. No retry/fallback.
"""
from dataclasses import dataclass
from urllib.parse import urlsplit
FIXED_BASE='https://hsn-ai-proxy.onrender.com'
PROVIDERS=frozenset(('gemini','groq','mistral'))
# Intentionally EMPTY. No enabled aliases based on client comments/model guesses.
MODEL_CATALOG=()
PORTS=frozenset('INNSA INBOM INMUN INIXY INMAA INENR INCOK INTUT INNML INVTZ INPRT INHAL SGSIN CNSHA CNNGB CNSZX CNTSN CNTAO HKHKG KRPUS JPYOK TWKHH MYPKG MYTPP LKCMB AEJEA NLRTM BEANR DEHAM DEBRV ESVLC ESALG GRPIR GBFXT USLAX USLGB USNYC USSAV USHOU BRSSZ ZADUR EGSUZ'.split())
MAX_REQUEST_BYTES=16384
MAX_RESPONSE_BYTES=1048576
TRANSPORT_SECONDS=20
class ConnectorRefused(ValueError):pass
@dataclass(frozen=True)
class ModelEntry:
 provider:str
 model:str
 owner_reference:str
 vendor_reference:str
 free_entitlement_reference:str
 observed_at:int
 expires_at:int

def plan_ai(provider,model,*,now):
 # Catalog is a source-controlled disabled tuple, not caller or environment input.
 if type(provider)is not str or provider not in PROVIDERS or type(model)is not str or type(now)is not int:raise ConnectorRefused('Closed model selection required')
 matches=[e for e in MODEL_CATALOG if type(e)is ModelEntry and e.provider==provider and e.model==model]
 if len(matches)!=1:raise ConnectorRefused('Model catalog disabled or unverified')
 e=matches[0]
 if not all(type(v)is str and 1<=len(v)<=200 and all(33<=ord(c)<=126 for c in v)for v in (e.owner_reference,e.vendor_reference,e.free_entitlement_reference))or type(e.observed_at)is not int or type(e.expires_at)is not int or not 0<=e.observed_at<=now<e.expires_at<=e.observed_at+3600:raise ConnectorRefused('Fresh verified catalog required')
 if not 1<=len(model)<=100 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-/'for c in model):raise ConnectorRefused('Bounded model identifier required')
 path={'groq':'/groq/openai/v1/chat/completions','mistral':'/mistral/v1/chat/completions'}.get(provider)
 if provider=='gemini':
  if '/'in model:raise ConnectorRefused('Exact Gemini model required')
  path='/gemini/v1beta/models/'+model+':generateContent'
 return {'base':FIXED_BASE,'path':path,'method':'POST','provider':provider,'model':model,'max_request_bytes':MAX_REQUEST_BYTES,'max_response_bytes':MAX_RESPONSE_BYTES,'timeout_seconds':TRANSPORT_SECONDS,'redirects':False,'retries':0,'fallbacks':0,'unit':'proxy_calls','provider_attempts':'unknown'}

def plan_ships(port):
 if type(port)is not str or port not in PORTS|{'ALL'}:raise ConnectorRefused('Exact closed port required')
 return {'base':FIXED_BASE,'path':'/ships?port='+port,'method':'GET','max_response_bytes':MAX_RESPONSE_BYTES,'timeout_seconds':TRANSPORT_SECONDS,'redirects':False,'retries':0,'unit':'proxy_calls','provider_attempts':0}

def validate_backend(values):
 if type(values)is not dict or any(type(k)is not str or type(v)is not str for k,v in values.items()):raise ConnectorRefused('Exact backend configuration required')
 if values.get('FINDER_PROXY_BASE_URL')!=FIXED_BASE:raise ConnectorRefused('Fixed proxy origin required')
 secret=values.get('FINDER_PROXY_SECRET','')
 if not 48<=len(secret)<=256 or any(ord(c)<33 or ord(c)>126 for c in secret):raise ConnectorRefused('Dedicated backend secret required')
 # Return no secret. This gate is not proof it matches APP_SECRET or is private.
 return {'configured':True,'transport_enabled':False,'base':FIXED_BASE}
