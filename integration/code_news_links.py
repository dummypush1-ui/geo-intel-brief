"""Pure, supplied-data bidirectional trade-news relationships. Not classification.

No API, DB, provider, storage, inference, automatic alias creation or UI wiring.
A review supplies exact catalogue identities and phrase rules. Commodity rules
point to broad headings, never silently manufacture a detailed national code.
"""
import re
import hashlib
from copy import deepcopy

EXPLICIT = re.compile(r'(?<!\w)(HSN|HS)\s*(?:code\s*)?[:#-]?\s*([0-9]{4}(?:[0-9]{2}){0,4})(?!\w|\s*[.\-/,]\s*\d|\s+\d)',re.I)
WHITESPACE = re.compile(r'\s+')
def explicit_mentions(source):
 """Linear whitespace normalization, original evidence offsets retained."""
 from bisect import bisect_right
 pieces=[];boundaries=[];deltas=[];last=0;removed=0
 for run in WHITESPACE.finditer(source):
  pieces.extend((source[last:run.start()], ' '))
  removed += run.end()-run.start()-1
  boundaries.append(run.end()-removed);deltas.append(removed)
  last=run.end()
 pieces.append(source[last:]);normalized=''.join(pieces)
 for hit in EXPLICIT.finditer(normalized):
  start=hit.start();end=hit.end()
  si=bisect_right(boundaries,start)-1;ei=bisect_right(boundaries,end)-1
  original_start=start+(deltas[si]if si>=0 else 0)
  original_end=end+(deltas[ei]if ei>=0 else 0)
  yield hit.group(1),hit.group(2),source[original_start:original_end]

class Refused(ValueError):pass

def text(value,cap):
 if type(value)is not str or not 1<=len(value)<=cap or any(ord(c)<32 and c not in '\n\t' for c in value):raise Refused('Bounded plain text required')
 return value

def identity(row):
 if type(row)is not dict or set(row)!={'system','edition','code','description'}:raise Refused('Exact catalogue fields')
 if not re.fullmatch('[A-Z]{2,3}',text(row['system'],3)):raise Refused('Exact system')
 if not re.fullmatch('[0-9]{4}(?:[0-9]{2}){0,4}',text(row['code'],12)):raise Refused('Exact 4/6/8/10/12 digit code')
 text(row['edition'],100);text(row['description'],4000)
 return row['system'],row['edition'],row['code']

def phrase(term,source):
 return re.search(r'(?<!\w)'+re.escape(term.casefold())+r'(?!\w)',source.casefold())is not None

class Links:
 def __init__(self,catalogue,rules,*,omissions=None):
  if type(catalogue)is not list or len(catalogue)>400000 or type(rules)is not list or len(rules)>500:raise Refused('Bounded catalogue and rules')
  self.catalogue={};self.rules=[];self.by_code={};self.omissions={}
  if omissions is not None:
   if type(omissions)is not list or len(omissions)>100000:raise Refused('Bounded omission ledger')
   for omitted in omissions:
    if type(omitted)is not dict or set(omitted)!={'system','edition','code','state'}or omitted['state']not in ('conflicting_source_rows','not_in_link_model','unusable_description'):raise Refused('Exact omission evidence')
    for field,cap in (('system',3),('edition',100),('code',12)):text(omitted[field],cap)
    if not re.fullmatch('[0-9]{2,12}',omitted['code']):raise Refused('Exact omitted code')
    key=tuple(omitted[k]for k in ('system','edition','code'))
    if key in self.omissions:raise Refused('Duplicate omitted identity')
    self.omissions[key]=omitted['state'];self.by_code.setdefault(key[2],[]).append(key)
  for row in catalogue:
   key=identity(row)
   if key in self.catalogue or key in self.omissions:raise Refused('Duplicate catalogue identity')
   self.catalogue[key]=deepcopy(row)
   self.by_code.setdefault(key[2],[]).append(key)
  ids=set()
  for rule in rules:
   if type(rule)is not dict or set(rule)!={'id','system','edition','code','commodity','phrases','trade_cues','exclude_phrases','source_description_sha256','review_state'}:raise Refused('Exact rule fields')
   key=tuple(rule[k]for k in ('system','edition','code'))
   target=self.catalogue.get(key)
   if target is None or len(key[2])!=4:raise Refused('Reviewed broad catalogue heading required')
   if rule['review_state']!='reviewed':raise Refused('Unreviewed rule')
   if rule['source_description_sha256']!=hashlib.sha256(target['description'].encode()).hexdigest():raise Refused('Rule source mismatch')
   rid=text(rule['id'],80);text(rule['commodity'],100)
   if rid in ids:raise Refused('Duplicate rule')
   ids.add(rid)
   for field in ('phrases','trade_cues','exclude_phrases'):
    values=rule[field]
    if type(values)is not list or len(values)>20 or (field!='exclude_phrases'and not values):raise Refused('Bounded evidence vocabulary')
    for value in values:text(value,80)
   self.rules.append(deepcopy(rule))
 def resolve(self,code,system=None,edition=None):
  if type(code)is not str or not re.fullmatch('[0-9]{2,12}',code):return {'state':'invalid_code','items':[]}
  keys=[k for k in self.by_code.get(code,[])if (system is None or k[0]==system)and(edition is None or k[1]==edition)]
  candidates=[dict(self.catalogue[k],state='resolved')if k in self.catalogue else dict(system=k[0],edition=k[1],code=k[2],state=self.omissions[k])for k in keys]
  if len(candidates)>1:return {'state':'ambiguous','items':candidates}
  if candidates:
   row=candidates[0];return {'state':row['state'],'items':[row]}
  if len(code)in (2,7,9,11):return {'state':'not_in_link_model','items':[]}
  return {'state':'unknown_code','items':[]}
 def for_news(self,article):
  if type(article)is not dict or not {'article_key','title','summary'}<=set(article):raise Refused('Article identity and content required')
  key=text(article['article_key'],100);title=text(article['title'],2000)
  if type(article['summary'])is not str or len(article['summary'])>16000:raise Refused('Bounded summary')
  source=title+'\n'+article['summary'];out=[]
  # Explicit attribution still is only a reported code mention. Missing system/
  # edition never selects the first of several national identities.
  for label,code,evidence in explicit_mentions(source):
   matches=self.resolve(code,'HS'if label.upper()=='HS'else'IN')
   # HSN means the India catalogue convention here, not proof of jurisdiction.
   # Four-digit mentions are offered only when the supplied edition resolves.
   if len(code)==4 and matches['state']!='resolved':continue
   out.append({'article_key':key,'kind':'reported_code_mention','resolution':matches['state'],'targets':matches['items'],'evidence':evidence,'legal_classification_verified':False})
  for rule in self.rules:
   matched=[t for t in rule['phrases']if phrase(t,source)]
   cues=[t for t in rule['trade_cues']if phrase(t,source)]
   if not matched or not cues or any(phrase(t,source)for t in rule['exclude_phrases']):continue
   target=self.catalogue[tuple(rule[k]for k in ('system','edition','code'))]
   out.append({'article_key':key,'kind':'commodity_context_suggestion','resolution':'reviewed_heading_context','targets':[deepcopy(target)],'rule_id':rule['id'],'evidence':{'commodity_phrases':matched,'trade_cues':cues},'legal_classification_verified':False})
  return {'state':'relationships'if out else'unassigned','items':out,'scope':'supplied_article_title_summary','not_exhaustive':True}
 def for_code(self,code,articles,system=None,edition=None):
  resolved=self.resolve(code,system,edition)
  if resolved['state']!='resolved':return dict(resolved,relationships=[])
  target=resolved['items'][0]
  if type(articles)is not list or len(articles)>1000:raise Refused('Bounded supplied article page')
  relationships=[]
  for article in articles:
   for link in self.for_news(article)['items']:
    for linked in link['targets']:
     if linked['system']!=target['system']or linked['edition']!=target['edition']:continue
     exact=linked['code']==code
     family=link['kind']=='commodity_context_suggestion'and code.startswith(linked['code'])
     if exact or family:
      relationships.append(dict(link,query_code=deepcopy(target),relation_scope='same_code_mention'if link['kind']=='reported_code_mention'else'exact_heading_context'if exact else'broader_heading_context_not_subheading_proof'))
      break
  return {'state':'relationships'if relationships else'no_evidence_in_supplied_page','items':resolved['items'],'relationships':relationships,'scope':'supplied_article_page_only','not_full_store_search':True}
