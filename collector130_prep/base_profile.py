"""Scratch installation profile; no env/client imports or production mounting."""
import ast,hashlib,math
from pathlib import Path
from collector113_prep.feed_composition import original_catalog
ROOT=Path(__file__).resolve().parents[1]
CONFIG_PIN='f7fbf007954c6918fbe2e402863fa29f597fe5d5cb4d60d1001deca8896b21f3'
class ProfileRefused(ValueError):pass

def defaults():
 raw=(ROOT/'intelligence/geo/config.py').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=CONFIG_PIN:raise ProfileRefused('Original config drift')
 tree=ast.parse(raw)
 found={}
 for node in tree.body:
  if type(node)is ast.Assign and len(node.targets)==1 and type(node.targets[0])is ast.Name:
   name=node.targets[0].id
   for call in ast.walk(node.value):
    if type(call)is ast.Call and type(call.func)is ast.Attribute and type(call.func.value)is ast.Name and call.func.value.id=='os' and call.func.attr=='getenv' and len(call.args)==2:
     key=ast.literal_eval(call.args[0]);value=ast.literal_eval(call.args[1])
     if name==key:found[key]=value
     break
 return found

def compile_profile(settings):
 """Only installation settings; no URI/secrets/source addresses in this shape.
 Production readiness explicitly false while adapters/role/health gates pending.
 """
 if type(settings)is not dict:raise ProfileRefused('Exact installation mapping')
 permitted={'MAX_ITEMS_PER_FEED','REQUEST_TIMEOUT','LOOKBACK_HOURS','ACTIVE_CATEGORIES','DEDUPE_THRESHOLD','ENABLE_FULL_TEXT','ENABLE_GNEWS','ENABLE_TELEGRAM_BACKUP'}
 if set(settings)-permitted or any(type(v)is not str or len(v)>2000 for v in settings.values()):raise ProfileRefused('Unsupported installation settings')
 original=defaults();s={k:settings.get(k,original[k])for k in permitted}
 try:
  cap=int(s['MAX_ITEMS_PER_FEED']);timeout=int(s['REQUEST_TIMEOUT']);hours=int(s['LOOKBACK_HOURS']);threshold=float(s['DEDUPE_THRESHOLD'])
 except ValueError:raise ProfileRefused('Config parse')from None
 if not 1<=cap<=200 or not 1<=timeout<=30 or not 1<=hours<=168 or not math.isfinite(threshold) or not 0<threshold<=1:raise ProfileRefused('Unsupported bounded config')
 categories=[x.strip().upper()for x in s['ACTIVE_CATEGORIES'].split(',')if x.strip()]
 allowed={'GEOPOLITICS','CONFERENCE','TRADE','SANCTIONS','RISK','RESEARCH','GENERAL'}
 if not categories or set(categories)-allowed or len(categories)>20:raise ProfileRefused('Category config')
 # Original .lower()==true semantics, not arbitrary truthiness.
 flags={k:s[k].lower()=='true'for k in ('ENABLE_FULL_TEXT','ENABLE_GNEWS','ENABLE_TELEGRAM_BACKUP')}
 gates=['live_dns_tls_health','runtime_isolation','mongo_role_index_ttl','write_reconciliation','service_mount','trigger_owner','free_capacity']
 gates += [k.lower()+'_adapter'for k,v in flags.items()if v]
 return {'scope':'inactive_installed_geo_profile','feeds':original_catalog(),'max_items':cap,'timeout':timeout,'lookback_hours':hours,'active_categories':categories,'threshold':threshold,'source_flags':flags,'pending_gates':gates,'production_ready':False,'delivery':False}
