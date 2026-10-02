"""Agencia Gov offline article parser. No fetch, writes, or source enablement.

EBC terms restrict portal use to personal/noncommercial purposes. Supplying
reviewed robots text is a fixture gate, not proof of purpose/reuse permission.
Only structural hiddenness is evaluated; no images or page framing emitted.
"""
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from integration.news_view import safe_url,date_view
from integration.scraper_policy import can_fetch
RULE={'name':'Agência Gov','url':'https://agenciagov.ebc.com.br/','country':'Brazil','article_path_prefix':'/noticias/'}
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

def article_url(url):
 value=safe_url(url)
 if not value:return None
 u=urlsplit(value)
 if u.scheme!='https' or u.netloc!='agenciagov.ebc.com.br' or u.query or u.fragment or not re.fullmatch(r'/noticias/\d{6}/[a-z0-9][a-z0-9-]*',u.path):return None
 return value

class AgenciaArticle(HTMLParser):
 def __init__(self):
  super().__init__(convert_charrefs=True);self.stack=[];self.hidden=[];self.root=None;self.body_root=None;self.title_root=None;self.root_count=0;self.body_count=0;self.title_count=0;self.root_closed=False;self.body_closed=False;self.title_closed=False;self.title=[];self.body=[];self.og=[];self.og_urls=[];self.created=[];self.error=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs);depth=len(self.stack)+1
  if tag=='meta' and 'head' in self.stack:
   if a.get('property')=='og:title':self.og.append(' '.join((a.get('content') or '').split()))
   if a.get('property')=='og:url':self.og_urls.append(a.get('content'))
   if a.get('name')=='DC.date.created':self.created.append(a.get('content'))
  if tag in VOID:
   if tag=='br' and self.body_root and not self.hidden:self.body.append('\n')
   return
  self.stack.append(tag)
  if tag in ('script','style','nav','aside','footer') or 'hidden' in a or a.get('aria-hidden','').strip().casefold()=='true':self.hidden.append(depth)
  if tag=='article' and a.get('id')=='content':
   self.root_count+=1
   if self.root_count!=1 or self.hidden:self.error=True
   self.root=depth
  if self.root:
   if tag=='h1' and 'titulo-noticia-conteudo' in a.get('class','').split():
    self.title_count+=1
    if self.title_count!=1 or self.hidden:self.error=True
    self.title_root=depth
   if tag=='div' and 'texto-conteudo' in a.get('class','').split():
    self.body_count+=1
    if self.body_count!=1 or self.hidden or self.title_root:self.error=True
    self.body_root=depth
   if self.body_root and tag in ('p','h2','h3','li'):self.body.append('\n')
 def handle_data(self,data):
  if self.hidden:return
  if self.title_root:self.title.append(data)
  if self.body_root:self.body.append(data)
 def handle_endtag(self,tag):
  if tag in VOID:return
  if tag not in self.stack:
   if self.root:self.error=True
   return
  depth=len(self.stack)
  if self.stack[-1]!=tag:
   if self.root or self.hidden:self.error=True
   index=len(self.stack)-1-self.stack[::-1].index(tag);self.stack=self.stack[:index];return
  if self.title_root==depth:self.title_root=None;self.title_closed=True
  if self.body_root==depth:self.body_root=None;self.body_closed=True
  if self.root==depth:self.root=None;self.root_closed=True
  if self.hidden and self.hidden[-1]==depth:self.hidden.pop()
  self.stack.pop()
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if tag not in VOID:self.handle_endtag(tag)
 def result(self,url,observed_at):
  title=' '.join(''.join(self.title).split());text='\n'.join(' '.join(line.split()) for line in ''.join(self.body).splitlines() if line.strip())
  if self.error or self.hidden or not self.root_closed or not self.title_closed or not self.body_closed or self.root_count!=1 or self.body_count!=1 or self.title_count!=1:raise ValueError('Ambiguous or incomplete article structure')
  if not title or not self.og or any(t!=title for t in self.og) or not self.og_urls or any(u!=url for u in self.og_urls) or len(text)<100:raise ValueError('Article metadata/body mismatch')
  stamp=date_view(observed_at)
  if not stamp:raise ValueError('Zoned observation timestamp required')
  # DC.date.created is creation metadata, not necessarily public publication.
  created=[date_view(v) for v in self.created]
  source_created=created[0] if created and all(v==created[0] for v in created) else None
  return {'title':title[:500],'url':url,'source':RULE['name'],'country':'Brazil','category':'GENERAL','summary':text[:16000],'published':'','source_created_at':source_created,'collected_at':stamp,'method':'agenciagov_html_fixture','attribution':'Agência Gov / EBC','text_format':'plain','title_truncated':len(title)>500,'body_truncated':len(text)>16000}

def agencia_article(html,url,observed_at,robots_text,reviewed=False):
 url=article_url(url)
 if not url or not can_fetch({**RULE,'enabled':reviewed,'reviewed':reviewed},url,robots_text):raise ValueError('Reviewed exact article route required')
 if not isinstance(html,str) or len(html)>2_000_000:raise ValueError('Bounded HTML required')
 p=AgenciaArticle();p.feed(html);p.close();return p.result(url,observed_at)
