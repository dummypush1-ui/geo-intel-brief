"""Default-OFF supplied player ended/error/manual retry served-copy seam."""
import hashlib
from pathlib import Path
from flask import Response,request
from integration import public_brics_streams as base
ROOT=Path(__file__).resolve().parents[2];FLAG='PUBLIC_BRICS_RECOVERY_ENABLED'
BASE_SHA='e8e2fe52fed120a76c570bd7dab65cf7a9ebe2bc5338142df8dd8ed5a254c0a6'
RECOVERY_SHA='8e0359f91bbbd55f06e3c7f9dbe80bf1bd86d892384518d5adc539ff03b86652'
class Held(ValueError):pass

def transform(source,recovery):
 if hashlib.sha256(source.encode()).hexdigest()!=BASE_SHA or hashlib.sha256(recovery.encode()).hexdigest()!=RECOVERY_SHA:raise Held('Recovery source drift')
 changes={"'?autoplay=1&mute=1&playsinline=1&rel=0';":"'?autoplay=1&mute=1&playsinline=1&rel=0&enablejsapi=1&origin='+encodeURIComponent(location.origin);",'function mini(tile,c){':'function mini(tile,c){if(tile.dataset.recoveryHeld===\'true\')return;','function selectedPlayer(){const target=el(\'selected\'),':'function selectedPlayer(){const target=el(\'selected\');target.removeAttribute(\'data-recovery-held\');const '}
 for old,new in changes.items():
  if source.count(old)!=1:raise Held('Recovery served-copy seam drift')
  source=source.replace(old,new,1)
 return source+'\n'+recovery+'\ninstallRecovery(document,window);\n'

def prepare(env):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 value=env.get(FLAG,'false')
 if value not in ('true','false'):raise Held('Exact BRICS recovery flag required')
 if value=='false':return False
 if env.get(base.FLAG)!='true'or env.get('PREVIEW_PUBLIC_SAMPLE_ENABLED')!='true':raise Held('Public supplied video wall required')
 transform((ROOT/'integration/ui/public_brics_streams.js').read_text(),(ROOT/'integration/brics_recovery_b4/recovery.js').read_text())
 return True

def install(app):
 if app.extensions.get('public_brics_streams')is not True or 'brics_recovery_b4'in app.extensions:raise Held('Existing supplied video wall mount required')
 source=transform((ROOT/'integration/ui/public_brics_streams.js').read_text(),(ROOT/'integration/brics_recovery_b4/recovery.js').read_text());old=app.view_functions['assets']
 def assets(name):
  if name=='brics_streams.js':return Response(''if request.method=='HEAD'else source,mimetype='application/javascript')
  return old(name)
 app.view_functions['assets']=assets;app.extensions['brics_recovery_b4']=True
