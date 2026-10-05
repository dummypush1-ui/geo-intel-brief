"""Offline single-page change snapshots. No fetching, storage or email sends.

First observation establishes a baseline, never a change notification. Persist
snapshots separately from legacy articles; callers decide reviewed activation.
"""
from html.parser import HTMLParser
from html import escape
import hashlib,difflib,re,unicodedata
from datetime import datetime,timezone
from urllib.parse import urlsplit,urlunsplit

class VisibleText(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.stack=[];self.malformed_hidden=False;self.hidden_depth=0;self.events=0
 def _event(self):
  self.events+=1
  if self.events>8000:raise ValueError("Page event budget")
 def handle_comment(self,data):self._event()
 def handle_decl(self,data):self._event()
 def handle_pi(self,data):self._event()
 def unknown_decl(self,data):self._event()
 def handle_starttag(self,tag,attrs):
  self._event()
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
  self._event()
  for i in range(len(self.stack)-1,-1,-1):
   if self.stack[i][0]==tag:
    if any(hidden for _,hidden in self.stack[i+1:]):self.malformed_hidden=True
    self.hidden_depth-=sum(hidden for _,hidden in self.stack[i:])
    self.stack=self.stack[:i];break
 def handle_data(self,data):
  self._event()
  if not self.hidden_depth:
   text=' '.join(data.split())
   if text:self.parts.append(text)

MAX_HTML_BYTES=128*1024
MAX_TEXT_BYTES=2_000_000
MAX_LINES=20000
MAX_LINE_CHARS=100000
DIFF_LINES=1000
DIFF_BYTES=100000
KEYS={'url','observed_at','text','sha256','method'}

def _url(value):
 if type(value) is not str or not 1<=len(value)<=2048 or any(c.isspace() or ord(c)<32 or ord(c)==127 or c=='\\' for c in value):raise ValueError('Invalid page URL')
 try:
  value.encode("utf-8")
  u=urlsplit(value);host=u.hostname;port=u.port
  if u.scheme.lower() not in ('http','https') or not host or not host.isascii() or u.username is not None or u.password is not None:raise ValueError()
  authority=host.lower()
  if ':' in authority:authority='['+authority+']'
  if port is not None and port!=(443 if u.scheme.lower()=='https' else 80):authority+=':'+str(port)
  return urlunsplit((u.scheme.lower(),authority,u.path or '/',u.query,''))
 except (ValueError,UnicodeError):raise ValueError('Invalid page URL') from None

def _stamp(value):
 if type(value) is not str or not 1<=len(value)<=64:raise ValueError('Invalid observation timestamp')
 try:
  d=datetime.fromisoformat(value.replace('Z','+00:00'))
  if d.tzinfo is None or not 1970<=d.year<=2100:raise ValueError()
  d=d.astimezone(timezone.utc)
  if not 1970<=d.year<=2100:raise ValueError()
  return d.isoformat(timespec='microseconds')
 except (ValueError,OverflowError):raise ValueError('Invalid observation timestamp') from None

def _text(value):
 if type(value) is not str or len(value)>MAX_TEXT_BYTES:raise ValueError('Bounded page text required')
 try:encoded=value.encode('utf-8')
 except UnicodeError:raise ValueError('Invalid page text') from None
 if not 30<=len(value) or len(encoded)>MAX_TEXT_BYTES:raise ValueError('Bounded page text required')
 lines=value.splitlines()
 if len(lines)>MAX_LINES or any(len(line)>MAX_LINE_CHARS for line in lines):raise ValueError('Bounded page lines required')
 return encoded,lines

def snapshot(url,html,observed_at):
 url=_url(url);stamp=_stamp(observed_at)
 if type(html) is not str or len(html)>MAX_HTML_BYTES:raise ValueError('Bounded HTML required')
 try:
  if len(html.encode('utf-8'))>MAX_HTML_BYTES:raise ValueError()
  if html.count('<')>4000:raise ValueError()
  # Conservative delimiter spans, not an HTML tokenizer. Bounds giant
  # attributes/comments and text runs before HTMLParser scans them.
  if any(len(part)>4096 for part in re.split('[<>]',html)):raise ValueError()
 except (ValueError,UnicodeError):raise ValueError('Bounded HTML required') from None
 parser=VisibleText()
 try:parser.feed(html);parser.close()
 except Exception:raise ValueError('Malformed page HTML; retain previous baseline') from None
 if parser.malformed_hidden or any(hidden for _,hidden in parser.stack):raise ValueError('Unclosed hidden element; retain previous baseline')
 text='\n'.join(parser.parts);encoded,_=_text(text)
 return validate_snapshot({'url':url,'observed_at':stamp,'text':text,'sha256':hashlib.sha256(encoded).hexdigest(),'method':'page_change_snapshot'})

def validate_snapshot(value):
 if type(value) is not dict or any(type(k) is not str for k in value) or set(value)!=KEYS or any(type(value[k]) is not str for k in KEYS):raise ValueError('Invalid snapshot shape')
 encoded,_=_text(value['text'])
 if not re.fullmatch('[0-9a-f]{64}',value['sha256']) or hashlib.sha256(encoded).hexdigest()!=value['sha256'] or value['method']!='page_change_snapshot':raise ValueError('Invalid snapshot integrity')
 return {'url':_url(value['url']),'observed_at':_stamp(value['observed_at']),'text':value['text'],'sha256':value['sha256'],'method':value['method']}

def compare(previous,current):
 current=validate_snapshot(current)
 if previous is None:return {'state':'baseline','items':[],'snapshot':current}
 previous=validate_snapshot(previous)
 if previous.get('url')!=current.get('url'):raise ValueError('Page identity mismatch')
 if current['observed_at']<previous['observed_at']:raise ValueError('New observation must be later than baseline')
 if current['observed_at']==previous['observed_at'] and current['sha256']!=previous['sha256']:raise ValueError('Conflicting equal-time observation')
 if previous.get('sha256')==current.get('sha256'):return {'state':'unchanged','items':[],'snapshot':current}
 old_bytes,old_lines=_text(previous['text']);new_bytes,new_lines=_text(current['text'])
 controls_present=any(unicodedata.category(c) in ("Cc","Cf","Zl","Zp") and c not in "\n\r\t" for c in previous["text"]+current["text"])
 omitted=controls_present or max(len(old_lines),len(new_lines))>DIFF_LINES or max(len(old_bytes),len(new_bytes))>DIFF_BYTES
 diff=['[Page changed; diff omitted due to bounded comparison budget. Review source page.]'] if omitted else list(difflib.unified_diff(old_lines,new_lines,fromfile='previous observation',tofile='current observation',lineterm=''))
 change_id=hashlib.sha256((current['url']+'\n'+previous['sha256']+'\n'+current['sha256']+'\n'+previous['observed_at']).encode()).hexdigest()
 row={'id':change_id,'title':'Page changed: Nilgiris Economic Dialogue','url':current['url'],'source':'Nilgiried page watch','country':'India','category':'GENERAL','summary':'\n'.join(diff[:80])[:12000]+ ('\n[Diff truncated. Review source page.]' if len(diff)>80 else ''),'summary_html':escape('\n'.join(diff[:80])[:12000]),'summary_format':'plain_text','published':'','created_at':current['observed_at'],'method':'page_change','previous_sha256':previous['sha256'],'current_sha256':current['sha256'],'emailed':False}
 return {'state':'changed','items':[row],'snapshot':current,'diff_truncated':len(diff)>80,'diff_omitted':omitted}
