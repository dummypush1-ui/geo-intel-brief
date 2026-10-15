"""Exact candidate offline safety render, held until consumer review.
No public route, source repin, device storage, server or network operation.
"""
import hashlib,re
from integration.finder_offline import _candidate_safety_shell
FLAG='MERGED_FINDER_SAFE_RENDER_PREP_ENABLED'
class Held(ValueError):pass

def prepare(env,*,source=None,source_sha256=None):
 if type(env)is not dict or any(type(k)is not str or type(v)is not str for k,v in env.items()):raise Held('Plain environment strings required')
 flag=env.get(FLAG,'false')
 if flag not in ('true','false'):raise Held('Exact candidate safety flag required')
 if flag=='false':return None
 if type(source)is not str or type(source_sha256)is not str or not re.fullmatch('[a-f0-9]{64}',source_sha256):raise Held('Exact offline source bytes and SHA256 required')
 try:raw=source.encode('utf8')
 except UnicodeError:raise Held('UTF-8 candidate required')from None
 if len(raw)>40*1024*1024 or hashlib.sha256(raw).hexdigest()!=source_sha256:raise Held('Candidate source byte/hash boundary')
 try:rendered=_candidate_safety_shell(source)
 except Exception:raise Held('Candidate safety seam drift; last-good unchanged')from None
 # These are safety rewrite invariants, not a claim every feature is certified.
 if 'localStorage'in rendered or "const fetch = async()=>{throw new Error('Offline snapshot: live network disabled');};"not in rendered or 'const OFFLINE_STORE = {getItem(){return null;},setItem(){},removeItem(){}};'not in rendered or 'finder-shortlist-scroll'not in rendered or 'const probe = text.replace'not in rendered or 'Content-Security-Policy'not in rendered or "connect-src 'none'"not in rendered:raise Held('Candidate safety invariant missing')
 for name in ('AI_PROXY_URL','AIS_PROXY_URL','BUILTIN_GEMINI_KEYS','BUILTIN_GROQ_KEYS','BUILTIN_MISTRAL_KEYS','BUILTIN_NVIDIA_KEYS'):
  if not re.search(r'const\s+'+name+r"\s*=\s*''",rendered):raise Held('Candidate provider capability not removed')
 return {'state':'held_candidate_offline_safety_render_not_mounted','source_sha256':source_sha256,'rendered_sha256':hashlib.sha256(rendered.encode()).hexdigest(),'bytes':len(rendered.encode()),'network_disabled':True,'keys_removed':True,'device_storage_disabled':True,'csv_formula_safe':True,'shortlist_wrap':True,'writes':False,'published':False,'runtime_repin':False},rendered
