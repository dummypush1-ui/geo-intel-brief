"""Site-specific offline HTML parsers. No network or enablement decisions."""
from html.parser import HTMLParser
from urllib.parse import urljoin,urlsplit
from integration.news_view import safe_url,date_view
from integration.scraper_policy import ArticleLinks,can_fetch

SANews={'name':'SA Government News','url':'https://www.sanews.gov.za/','country':'South Africa','article_path_prefix':'/south-africa/'}

def sanews_listing(html,robots_text,reviewed=False):
 if not isinstance(html,str) or len(html)>2_000_000:raise ValueError('Bounded HTML required')
 rule={**SANews,'reviewed':reviewed,'enabled':reviewed}
 parser=ArticleLinks();parser.feed(html);parser.close()
 return parser.articles(rule,robots_text)

class SANewsArticle(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.depth=0;self.article_depth=None;self.h1=0;self.p=0;self.ignore=0;self.title=[];self.body=[];self.current=[];self.published=None;self.head=0;self.title_done=False;self.article_nesting=0;self.root_closed=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag not in ('br','img','meta','link','input','hr','source','wbr'):self.depth+=1
  if tag=='head':self.head+=1
  if tag=='meta' and self.head and self.published is None and a.get('property')=='article:published_time':
   value=a.get('content') or ''
   if value.endswith('Z') or '+' in value[10:]:self.published=date_view(value)
  if tag=='article' and 'node-detail' in a.get('class','').split() and self.article_depth is None:self.article_depth=self.depth
  if tag=='article' and self.article_depth is not None:
   self.article_nesting+=1
   if self.article_nesting>1:self.ignore+=1
  if tag=='h1' and not self.title_done:self.h1+=1
  if self.article_depth is not None:
   if tag in ('script','style','nav'):self.ignore+=1
   if tag=='p':self.p+=1;self.current=[]
   if tag=='br' and self.p:self.current.append(' ')
   # Publication comes only from exact, zoned article metadata, never card times.
 def handle_data(self,data):
  if self.h1:self.title.append(data)
  if self.article_depth is not None and self.p and not self.ignore:self.current.append(data)
 def handle_startendtag(self,tag,attrs):
  self.handle_starttag(tag,attrs)
  if tag not in ('br','img','meta','link','input','hr','source','wbr'):self.handle_endtag(tag)
 def handle_endtag(self,tag):
  if tag in ('br','img','meta','link','input','hr','source','wbr'):return
  if self.article_depth is not None:
   if tag=='p' and self.p:
    text=' '.join(''.join(self.current).split())
    if text and not self.ignore:self.body.append(text)
    self.p-=1;self.current=[]
   if tag in ('script','style','nav'):self.ignore=max(0,self.ignore-1)
   if tag=='article':
    self.article_nesting-=1
    if self.article_nesting>0:self.ignore=max(0,self.ignore-1)
    else:self.article_depth=None;self.p=0;self.current=[];self.ignore=0;self.root_closed=True
  if tag=='h1' and self.h1:self.h1=0;self.title_done=True
  if tag=='head':self.head=max(0,self.head-1)
  self.depth=max(0,self.depth-1)
 def result(self,url,observed_at):
  url=safe_url(url);title=' '.join(''.join(self.title).split());text='\n'.join(self.body)
  if not url or urlsplit(url).netloc!='www.sanews.gov.za' or not urlsplit(url).path.startswith('/south-africa/') or '..' in urlsplit(url).path.split('/') or '%' in urlsplit(url).path:raise ValueError('Expected SAnews article URL')
  if not self.root_closed:raise ValueError('Truncated article root; retain previous result')
  if not title or len(text)<100:raise ValueError('Article body/title missing; never emit homepage stub')
  stamp=date_view(observed_at)
  if not stamp:raise ValueError('Observation timestamp required')
  return {'title':title[:500],'url':url,'source':SANews['name'],'country':'South Africa','category':'GENERAL','summary':text[:16000],'published':self.published or '', 'collected_at':stamp,'method':'sanews_html_fixture','attribution':'SAnews','text_format':'plain','body_truncated':len(text)>16000,'title_truncated':len(title)>500}

def sanews_article(html,url,observed_at,robots_text,reviewed=False):
 if not can_fetch({**SANews,'enabled':reviewed,'reviewed':reviewed},url,robots_text):raise ValueError('Reviewed robots policy required')
 if not isinstance(html,str) or len(html)>2_000_000:raise ValueError('Bounded HTML required')
 parser=SANewsArticle();parser.feed(html);parser.close();return parser.result(url,observed_at)
