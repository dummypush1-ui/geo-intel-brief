"""D2 coverage candidate, unwired pure fixture. No News store/lock/IO."""
import secrets,time,json
from threading import Lock
class Refused(ValueError):pass
class PageBusy(Exception):pass
class PageExpired(Exception):pass
class PageUnavailable(Exception):pass
class SharedBudget:
 """Fixture-only admission model. Actual shared News admission is D2 work."""
 def __init__(self):self.lock=Lock();self.news=0;self.code=0
 def admit(self):
  if self.news+self.code>=16 or self.code>=4:raise Refused('shared_capacity')
  self.code+=1
 def release(self):
  if self.code<=0:raise Refused('double_release')
  self.code-=1
class Scan:
 def __init__(self,parent,match,budget,clock=time.monotonic,token_factory=lambda:secrets.token_urlsafe(32)):
  self.parent=parent;self.match=match;self.budget=budget;self.clock=clock;self.tokens=token_factory;self.states={};self.minute=None;self.calls=0
 def _drop(self,key,s):
  if key not in self.states:return
  del self.states[key]
  try:
   if s['parent'] is not None:self.parent.close(s['parent'])
  finally:
   if s['admitted']:self.budget.release();s['admitted']=False
 def _sweep(self,now):
  for key,s in list(self.states.items()):
   if now-s['used']>=120:self._drop(key,s)
 def head(self):return {'state':'metadata_only'},200
 def page(self,token='',target=None):
  if not self.budget.lock.acquire(False):return {'state':'busy'},429
  try:
   now=self.clock();self._sweep(now)
   key=None;s=None
   if token:
    for k,row in self.states.items():
     if token in (row['next'],row['last']):key=k;s=row;break
    if s is None:return {'state':'expired_restart_from_zero'},410
    if target is not None and target!=s['target']:return {'state':'target_mismatch'},410
    # Replay precedes quota, does no parent call and has byte-identical fields.
    if token==s['last']:return json.loads(s['cached']),200
   elif target is None:raise Refused('target_required')
   needs_parent=s is None or not s['carry']
   minute=int(now//60)
   if minute!=self.minute:self.minute=minute;self.calls=0
   if needs_parent and self.calls>=20:return {'state':'quota_wait','retry_after':60},429
   new=s is None
   if new:
    try:self.budget.admit()
    except Refused:return {'state':'shared_capacity'},429
    key=self.tokens();s={'parent':None,'used':now,'pages':0,'rows':0,'target':target,'next':None,'last':None,'cached':None,'carry':[],'eof':False,'done':False,'admitted':True,'checked':0,'refused':0};self.states[key]=s
   try:
    if needs_parent:
     self.calls+=1
     try:reply=self.parent.page(s['parent'],{'project':'geo','query':'','category':'','country':'','sort':'newest'},100)
     except PageBusy:
      if new:self._drop(key,s)
      return {'state':'parent_busy'},429
     except PageExpired:self._drop(key,s);return {'state':'expired_restart_from_zero'},410
     except Exception:self._drop(key,s);return {'state':'source_unavailable'},503
     # Parent has advanced. Capture latest handle before any local validation.
     s['parent']=reply.get('next_cursor')
     rows=reply.get('items')
     if type(rows)is not list or len(rows)>100 or len(json.dumps(rows,ensure_ascii=False).encode())>2097152:raise Refused('page_byte_cap')
     if type(reply.get('exhausted'))is not bool:raise Refused('parent_shape')
     s['carry']=rows;s['pages']+=1;s['rows']+=len(rows);s['eof']=reply['exhausted']
    links=[];consumed=0;checked_this=0;refused_this=0
    for r in s['carry']:
     report=self.match(s['target'],r)
     if type(report)is not dict or set(report)!={'state','items','coverage','not_exhaustive'}or report['not_exhaustive']is not True:raise Refused('typed_match_report')
     if report['state']=='evidence_refused_mentions_limit':
      if report['items']!=[]or report['coverage']!='article_refused':raise Refused('refusal_shape')
      refused_this+=1
     elif report['state']=='checked':
      if type(report['items'])is not list or len(report['items'])>32 or report['coverage']!='bounded_explicit_mentions_checked':raise Refused('checked_shape')
      # One article is one page item carrying all <=32 evidence mentions.
      # Never slice a single article's evidence to the page-item limit.
      if report['items']:
       candidate=links+[{'article_key':r['article_key'],'relationships':report['items']}]
       if len(json.dumps(candidate,ensure_ascii=False).encode())>524288:raise Refused('reply_byte_cap')
       links=candidate
      checked_this+=1
     else:raise Refused('match_state')
     consumed+=1
     if len(links)>=25:break
    s['checked']+=checked_this;s['refused']+=refused_this
    s['carry']=s['carry'][consumed:]
    done=not s['carry'] and s['eof'];stop=not s['carry'] and s['pages']>=20 and not done
    next_token=None if done or stop else self.tokens()
    body={'state':'complete_mutable_read' if done else 'budget_stopped_incomplete' if stop else 'continue_scan','items':links,'public_rows_scanned':s['rows'],'next_cursor':next_token,'complete':done,'parent_pages':s['pages'],'scan_complete':done,'evidence_complete':False,'evidence_scope':'bounded_explicit_mentions_only_not_all_commodity_news','articles_checked':s['checked'],'articles_refused_mentions_limit':s['refused'],'articles_checked_this_page':checked_this,'articles_refused_this_page':refused_this,'coverage_gap':s['refused']>0,'coverage_message':str(s['refused'])+(' article refused for too many code mentions'if s['refused']==1 else' articles refused for too many code mentions')if s['refused']else'No mention-limit refusals so far; only explicit mentions are checked'}
    s.update(last=token or None,next=next_token,cached=json.dumps(body,ensure_ascii=False),used=now,done=done or stop)
    if done or stop:
     if s['parent'] is not None:self.parent.close(s['parent']);s['parent']=None
     if s['admitted']:self.budget.release();s['admitted']=False
    # Retain last reply for prior-token retry until idle expiry. First request
    # has no token, so first-lost reply needs a fresh scan, explicitly no resume.
    return body,200
   except Exception:self._drop(key,s);return {'state':'page_refused'},503
  finally:self.budget.lock.release()
