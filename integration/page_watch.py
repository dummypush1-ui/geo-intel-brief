"""Offline single-page change snapshots. No fetching, storage or email sends.

First observation establishes a baseline, never a change notification. Persist
snapshots separately from legacy articles; callers decide reviewed activation.
"""
from html.parser import HTMLParser
from html import escape
import hashlib,difflib
from integration.news_view import safe_url,date_view

class VisibleText(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.stack=[];self.malformed_hidden=False;self.hidden_depth=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);hidden=tag in ('head','script','style','noscript','template','nav','footer') or 'hidden' in a or (a.get('aria-hidden') or '').strip().lower()=='true' or 'display:none' in (a.get('style') or '').replace(' ','').lower() or 'visibility:hidden' in (a.get('style') or '').replace(' ','').lower()
  if tag in ('p','li'):
   for i in range(len(self.stack)-1,-1,-1):
    if self.stack[i][0]==tag:
     if any(hidden for _,hidden in self.stack[i+1:]):self.malformed_hidden=True
     self.hidden_depth-=sum(hidden for _,hidden in self.stack[i:])
     self.stack=self.stack[:i];break
  if tag not in ('img','br','meta','link','input','hr','source','wbr'):
   if len(self.stack)>=500:raise ValueError('Page nesting too deep')
   self.stack.append((tag,hidden));self.hidden_depth+=int(hidden)
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i][0]==tag:
    if any(hidden for _,hidden in self.stack[i+1:]):self.malformed_hidden=True
    self.hidden_depth-=sum(hidden for _,hidden in self.stack[i:])
    self.stack=self.stack[:i];break
 def handle_data(self,data):
  if not self.hidden_depth:
   text=' '.join(data.split())
   if text:self.parts.append(text)

def snapshot(url,html,observed_at):
 if not safe_url(url):raise ValueError('Safe page URL required')
 if not isinstance(html,str) or len(html)>2_000_000:raise ValueError('Bounded HTML required')
 stamp=date_view(observed_at)
 if stamp is None:raise ValueError('Observation timestamp required')
 parser=VisibleText()
 try:parser.feed(html);parser.close()
 except Exception:raise ValueError('Malformed page HTML; retain previous baseline') from None
 if parser.malformed_hidden or any(hidden for _,hidden in parser.stack):raise ValueError('Unclosed hidden element; retain previous baseline')
 text='\n'.join(parser.parts)
 if len(text)<30:raise ValueError('Page text too short; do not replace baseline')
 return {'url':safe_url(url),'observed_at':stamp,'text':text,'sha256':hashlib.sha256(text.encode()).hexdigest(),'method':'page_change_snapshot'}

def validate_snapshot(value):
 if not isinstance(value,dict) or any(not isinstance(value.get(k),str) for k in ('url','observed_at','text','sha256')):raise ValueError('Invalid snapshot shape')
 if not safe_url(value['url']) or not date_view(value['observed_at']) or hashlib.sha256(value['text'].encode()).hexdigest()!=value['sha256']:raise ValueError('Invalid snapshot identity/hash')

def compare(previous,current):
 validate_snapshot(current)
 if previous is None:return {'state':'baseline','items':[],'snapshot':current}
 validate_snapshot(previous)
 if previous.get('url')!=current.get('url'):raise ValueError('Page identity mismatch')
 if current['observed_at']<previous['observed_at']:raise ValueError('New observation must be later than baseline')
 if previous.get('sha256')==current.get('sha256'):return {'state':'unchanged','items':[],'snapshot':current}
 diff=list(difflib.unified_diff(previous['text'].splitlines(),current['text'].splitlines(),fromfile='previous observation',tofile='current observation',lineterm=''))
 change_id=hashlib.sha256((current['url']+'\n'+previous['sha256']+'\n'+current['sha256']+'\n'+previous['observed_at']).encode()).hexdigest()
 row={'id':change_id,'title':'Page changed: Nilgiris Economic Dialogue','url':current['url'],'source':'Nilgiried page watch','country':'India','category':'GENERAL','summary':'\n'.join(diff[:80])[:12000]+ ('\n[Diff truncated. Review source page.]' if len(diff)>80 else ''),'summary_html':escape('\n'.join(diff[:80])[:12000]),'summary_format':'plain_text','published':'','created_at':current['observed_at'],'method':'page_change','previous_sha256':previous['sha256'],'current_sha256':current['sha256'],'emailed':False}
 return {'state':'changed','items':[row],'snapshot':current,'diff_truncated':len(diff)>80}
