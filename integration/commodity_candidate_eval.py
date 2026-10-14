"""C1 synthetic-only offline candidate evaluator. No IO, routes or activation.
Not part of C1: real commodity rules/descriptions, legal classification, public
UI, production matcher/index changes, providers, DB, export or native sources.
Blocking supplied Python callbacks cannot be interrupted here. A timeout raised
by a callback is unavailable; this module makes no hard wall-clock guarantee.
"""
from dataclasses import dataclass
import hashlib,json,unicodedata
from integration.code_news_links import phrase
SYSTEMS=frozenset(('SYN','SYA','SYB'))
MAX_WORK=100000
MAX_BYTES=250000
MARKER='not legal / not exhaustive / heading context only'

def plain(v,cap):
 if type(v)is not str or not 1<=len(v)<=cap:raise ValueError()
 if any(unicodedata.category(c) in ('Cc','Cf','Cs') or c in '\u2028\u2029' for c in v):raise ValueError()
 v.encode('utf-8',errors='strict')
 return v

def terms(v,empty=False):
 if type(v)is not tuple or len(v)>20 or not empty and not v:raise ValueError()
 folded=[]
 for p in v:
  plain(p,80)
  if not any(c.isalnum()for c in p)or not p.strip()or p!=p.strip():raise ValueError()
  key=p.casefold()
  if key in folded:raise ValueError()
  folded.append(key)
 return v

@dataclass(frozen=True,slots=True)
class HeadingSnapshot:
 system:str
 edition:str
 code:str
 description:str

def heading(v):
 if type(v)is not HeadingSnapshot:raise ValueError()
 if v.system not in SYSTEMS or (v.edition,v.code)!=('fixture-only','9999'):raise ValueError()
 plain(v.description,4000)
 if not v.description.startswith('Synthetic fixture: '):raise ValueError()
 return hashlib.sha256(v.description.encode('utf-8')).hexdigest()

@dataclass(frozen=True,slots=True)
class DraftRule:
 id:str
 system:str
 edition:str
 code:str
 description_sha256:str
 phrases:tuple
 trade_cues:tuple
 exclude_phrases:tuple
 review_refs:tuple=()

def validate_rule(r):
 if type(r)is not DraftRule:raise ValueError()
 plain(r.id,80)
 if r.system not in SYSTEMS or (r.edition,r.code)!=('fixture-only','9999'):raise ValueError()
 if type(r.description_sha256)is not str or len(r.description_sha256)!=64 or any(c not in '0123456789abcdef' for c in r.description_sha256):raise ValueError()
 terms(r.phrases);terms(r.trade_cues);terms(r.exclude_phrases,True)
 if type(r.review_refs)is not tuple or len(r.review_refs)>10:raise ValueError()
 for ref in r.review_refs:plain(ref,200)
 return sum(map(len,(r.phrases,r.trade_cues,r.exclude_phrases)))

def evaluate(rules,articles,resolve):
 """Literal Unicode casefold + shared word-boundary phrase semantics.
 No stemming/ranking; duplicate phrases after casefold are refused. Callbacks
 receive exact synthetic identity once. Review refs never affect evaluation.
 """
 try:
  if type(rules)is not tuple or not 1<=len(rules)<=20 or type(articles)is not tuple or len(articles)>100 or not callable(resolve):raise ValueError()
  count=0;ids=set();identities=set()
  for r in rules:
   count+=validate_rule(r)
   if r.id in ids:raise ValueError()
   ids.add(r.id)
   # One rule per exact synthetic identity: no competing definitions selected.
   identity=(r.system,r.edition,r.code)
   if identity in identities:raise ValueError()
   identities.add(identity)
  if count>200 or count*len(articles)*3>MAX_WORK:raise ValueError()
  inputs=[dict(id=r.id,identity=[r.system,r.edition,r.code],description_sha256=r.description_sha256,phrases=r.phrases,trade_cues=r.trade_cues,exclude_phrases=r.exclude_phrases,review_refs=r.review_refs)for r in rules]
  if len(json.dumps(inputs,ensure_ascii=False,separators=(',',':')).encode('utf-8'))>MAX_BYTES:raise ValueError()
  clean=[];keys=set()
  for row in articles:
   if type(row)is not dict or set(row)!={'article_key','title','summary'}:raise ValueError()
   plain(row['article_key'],100);plain(row['title'],2000)
   if type(row['summary'])is not str:raise ValueError()
   if row['summary']!='':plain(row['summary'],8000)
   if row['article_key']in keys:raise ValueError()
   keys.add(row['article_key']);clean.append(dict(row))
  # Input UTF-8 byte budget checked before invoking any callback.
  if len(json.dumps(clean,ensure_ascii=False,separators=(',',':')).encode('utf-8'))>MAX_BYTES:raise ValueError()
  resolved={}
  for r in sorted(rules,key=lambda x:x.id):
   key=(r.system,r.edition,r.code)
   snap=resolve(*key);actual=heading(snap)
   if (snap.system,snap.edition,snap.code)!=key or actual!=r.description_sha256:raise ValueError()
   resolved[key]=actual
  results=[]
  for a in sorted(clean,key=lambda x:x['article_key']):
   candidates=[]
   for r in sorted(rules,key=lambda x:x.id):
    fields=('title','summary')
    evidence=lambda ts:[dict(phrase=t,source_field=f)for t in sorted(ts,key=lambda x:(x.casefold(),x))for f in fields if phrase(t,a[f])]
    matched=evidence(r.phrases);cues=evidence(r.trade_cues);excluded=evidence(r.exclude_phrases)
    if not matched or not cues or excluded:continue
    candidates.append(dict(rule_id=r.id,target=dict(system=r.system,edition=r.edition,code=r.code),description_sha256=resolved[(r.system,r.edition,r.code)],matched_phrases=matched,trade_cues=cues,legal_classification_verified=False,warning=MARKER))
   results.append(dict(article_key=a['article_key'],state='ambiguous_candidates'if len(candidates)>1 else 'candidate_not_enabled',candidates=candidates))
  body=dict(state='candidate_not_enabled',review_refs_state='supplied_unverified',legal_classification_verified=False,warning=MARKER,items=results)
  if len(json.dumps(body,ensure_ascii=False,separators=(',',':')).encode('utf-8'))>MAX_BYTES:raise ValueError()
  return body
 except Exception:return {'state':'unavailable'}
