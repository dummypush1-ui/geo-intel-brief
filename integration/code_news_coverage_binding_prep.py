"""Dormant fixed code pins. Injected binding is eligibility, never owner authority.
No provider/request/env can choose pins, index path or matcher version. Activation
still needs independent owner DB scope/deployment/abuse evidence, held separately.
"""
import hashlib,json
from pathlib import Path
from dataclasses import dataclass
ROOT=Path(__file__).resolve().parents[1]
PINS={'integration/code_news_index/manifest.json':'6edbda1415380b9b99f1f28a79ced563cd72b3ab4ab6323a35cfd531b62e17ea','integration/code_news_links.py':'12fd8e76fca034740d4578e4ee6b1a48db2991e86a23ef15669138a0aec708c2','integration/code_news_coverage_broker_prep.py':'bcfc6b8744350cdf9ab65dc27bf4d9adb34a421b0a66be5493d344218b83f5b9','integration/code_news_index/codes.idx':'4f6487562fd144ef42f75724581fc4d206bf2f0df7b78ce6c66270bffff3fb03','integration/code_news_index/rows.jsonl':'e258d3a5ae3f285ab135a0c262a30501135b59b8e7bcb3fdd0b0dcd802d1f502'}
PINS.update({'integration/code_news_parent_prep.py': '785cd35a04bfe16d22f264c96a4dbc7951e8b499746c738712ef5b3f3c26aef2', 'integration/code_news_disk.py': 'c7a77b1fc4569deabae2d110af861b7aa2b0c21b6e2dc14fdcadb6df014c53da', 'integration/news_pages.py': '24d25bb917c72f1601cfa7c1d667e6c6663e42f604a3e0f2db4de2c085cbb9f0'})
PINS['integration/code_news_coverage_route_prep.py']='0148993ae102d0ac9814d22b672f7d2ed68d19c79ef8b1f8a210772296196af3'
VERSION='explicit-C-linear-D2c-v2-wire-D3b-v1'
@dataclass(frozen=True)
class VerifiedPins:
 manifest:str
 matcher_version:str
 folder:Path
@dataclass(frozen=True)
class Binding:
 """Exact injected eligibility record, not proof of external facts or authority."""
 single_worker:bool
 source_timeout_reviewed:bool
 memory_reviewed:bool
 abuse_reviewed:bool
 owner_scope_ref:str
 deployment_ref:str

def verify_pins():
 try:
  for name,expected in PINS.items():
   h=hashlib.sha256()
   with (ROOT/name).open('rb')as f:
    while chunk:=f.read(65536):h.update(chunk)
   if h.hexdigest()!=expected:raise ValueError()
  meta=json.loads((ROOT/'integration/code_news_index/manifest.json').read_text())
  if meta['files']['codes.idx']['sha256']!=PINS['integration/code_news_index/codes.idx']or meta['files']['rows.jsonl']['sha256']!=PINS['integration/code_news_index/rows.jsonl']:raise ValueError()
  return VerifiedPins(PINS['integration/code_news_index/manifest.json'],VERSION,ROOT/'integration/code_news_index')
 except Exception:raise ValueError('Coverage pins unavailable')from None

def prepare(env,provider):
 from integration.code_news_coverage_ui_prep import enabled as ui_enabled
 from integration.code_news_coverage_route_prep import enabled as api_enabled
 ui=ui_enabled(env);api=api_enabled(env)
 if not api:return ui,False,None
 if env.get('PUBLIC_NEWS_READ_ENABLED')!='true'or env.get('PUBLIC_NEWS_FULL_PAGES_ENABLED')!='true'or not callable(provider):raise ValueError('Coverage binding required')
 pins=verify_pins() # Before provider/client/index/News construction.
 try:
  record=provider()
  if type(record)is not Binding or any(getattr(record,k)is not True for k in ('single_worker','source_timeout_reviewed','memory_reviewed','abuse_reviewed'))or any(type(getattr(record,k))is not str or not 1<=len(getattr(record,k))<=200 for k in ('owner_scope_ref','deployment_ref')):raise ValueError()
 except Exception:raise ValueError('Coverage binding unavailable')from None
 return ui,True,pins
