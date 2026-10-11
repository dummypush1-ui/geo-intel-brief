"""Unwired bounded coverage subclass. No app route/provider/DB construction."""
import json
from copy import deepcopy
from integration.code_news_parent_prep import Broker,Refused
from integration.code_news_links import explicit_mentions
class CoverageBroker(Broker):
 def __init__(self,*a,**kw):self.contexts={};super().__init__(*a,**kw)
 def _prune_locked(self):
  super()._prune_locked()
  for key in list(self.contexts):
   if key not in self.ledger.rows:self.contexts.pop(key,None)
 def _initialize_locked(self,active):self.contexts[active]={'carry':[],'eof':False,'pages':0,'checked':0,'refused':0,'unreadable':0,'received':0}
 def _need_parent_locked(self,active):return not self.contexts[active]['carry'] and not self.contexts[active]['eof']
 def _article(self,row,target):
  # Approved keys only. Private provider/source handles never pass through.
  if type(row)is not dict:return 'unreadable',[]
  key=row.get('article_key')
  if type(key)is not str or not 1<=len(key)<=100:return 'unreadable',[]
  title=row.get('title');summary=row.get('summary')
  title=''if title is None else title;summary=''if summary is None else summary
  if type(title)is not str or type(summary)is not str or len(title)>2000 or len(summary)>16000:return 'unreadable',[]
  title=title.replace('\r\n','\n').replace('\r','\n');summary=summary.replace('\r\n','\n').replace('\r','\n')
  if any(ord(c)<32 and c not in '\n\t'for c in title+summary):return 'unreadable',[]
  if self.model.rules:raise Refused('Explicit-only vocabulary required')
  hits=[]
  for hit in explicit_mentions(title+'\n'+summary):
   if len(hits)==32:return 'refused',[]
   hits.append(hit)
  # C owns code attribution and unresolved-heading rules. The newline-only
  # empty-title boundary adds no content, leaves summary in its original field.
  matched=self.model.for_news({'article_key':key,'title':title or '\n','summary':summary})
  out=[]
  for link in matched['items']:
   if link['kind']!='reported_code_mention' or link['resolution']!='resolved':continue
   for item in link['targets']:
    if all(item[k]==target[k]for k in ('system','edition','code')):
     out.append({'article_key':key,'kind':link['kind'],'target':deepcopy(item),'evidence':link['evidence'],'legal_classification_verified':link['legal_classification_verified']});break
  return 'checked',out
 def _finish_locked(self,active,reply):
  ctx=self.contexts[active];target=self.ledger.rows[active]['binding']['target']
  if reply is not None:
   if type(reply)is not dict or type(reply.get('items'))is not list or len(reply['items'])>100 or type(reply.get('exhausted'))is not bool:raise Refused('Malformed parent page')
   if len(json.dumps(reply['items'],ensure_ascii=False).encode())>2097152:raise Refused('Carry byte cap')
   ctx['carry']=deepcopy(reply['items']);ctx['eof']=reply['exhausted'];ctx['pages']+=1;ctx['received']+=len(reply['items'])
  items=[];consumed=0;counts={'checked':0,'refused':0,'unreadable':0}
  for row in ctx['carry'][:100]:
   state,relationships=self._article(row,target)
   if relationships:
    candidate=items+[{'article_key':row['article_key'],'relationships':relationships}]
    if len(json.dumps(candidate,ensure_ascii=False).encode())>500000:raise Refused('Reply payload cap')
    items=candidate
   counts[state]+=1;consumed+=1
   if len(items)>=25:break
  ctx['carry']=ctx['carry'][consumed:]
  for k,v in counts.items():ctx[k]+=v
  complete=ctx['eof']and not ctx['carry'];stop=ctx['pages']>=20 and not ctx['carry']and not complete
  def message(n,s):return str(n)+' article'+(''if n==1 else's')+' '+s
  body={'state':'complete_mutable_read'if complete else'budget_stopped_incomplete'if stop else'continue_scan','items':items,'scan_complete':complete,'evidence_complete':False,'evidence_scope':'bounded_explicit_mentions_only_not_all_commodity_news','coverage_gap':bool(ctx['refused']or ctx['unreadable']),'articles_checked':ctx['checked'],'articles_refused_mentions_limit':ctx['refused'],'articles_unreadable':ctx['unreadable'],'articles_checked_this_page':counts['checked'],'articles_refused_this_page':counts['refused'],'articles_unreadable_this_page':counts['unreadable'],'rows_consumed_this_page':consumed,'parent_pages':ctx['pages'],'public_rows_received':ctx['received'],'total_count':None,'coverage_message':message(ctx['refused'],'refused for too many code mentions')+'; '+message(ctx['unreadable'],'unreadable. These are coverage gaps.'),'consistency':'mutable_read_not_snapshot'}
  # Include headroom for tokens/manifest/version before broker caches reply.
  if len(json.dumps(body,ensure_ascii=False).encode())>520000:raise Refused('Reply byte cap')
  if stop:
   parent=self.ledger.rows[active]['parent']
   if parent in self.pages.streams:
    self.pages.streams[parent]['cursor'].close();self.pages.streams[parent]['eof']=True
  return body,complete or stop
