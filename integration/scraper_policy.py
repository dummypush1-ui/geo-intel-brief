"""Offline policy checks and fixture parsing. Does not make network requests."""
from urllib.parse import urlsplit,urljoin
from urllib.robotparser import RobotFileParser
from html.parser import HTMLParser
from integration.news_view import safe_url
USER_AGENT='GeoIntelBrief/1.0'
def same_site(url,base):
 a,b=urlsplit(url),urlsplit(base)
 return a.scheme==b.scheme and a.netloc.lower()==b.netloc.lower() and bool(a.hostname)
def can_fetch(rule,url,robots_text):
 if not rule.get('enabled') or not rule.get('reviewed'):return False
 if not safe_url(url) or not same_site(url,rule.get('url','')):return False
 if not rule.get('article_path_prefix') or not urlsplit(url).path.startswith(rule['article_path_prefix']):return False
 if not robots_text or not isinstance(robots_text,str):return False
 robots=RobotFileParser();robots.parse(robots_text.splitlines())
 return robots.can_fetch(USER_AGENT,url)
def response_policy(status,content_type,body,retry_after=None):
 if status in (401,403,429):return {'state':'stopped','retry_after':retry_after,'reason':'access_or_rate_limit'}
 if status!=200:return {'state':'unavailable','reason':'http_status'}
 if 'text/html' not in content_type.lower():return {'state':'stopped','reason':'not_html'}
 if len(body)>2_000_000:return {'state':'stopped','reason':'response_too_large'}
 lower=body.casefold()
 if any(x in lower for x in ('verify you are human','captcha','cf-chl-','just a moment...')):return {'state':'stopped','reason':'challenge'}
 return {'state':'ready'}
class ArticleLinks(HTMLParser):
 def __init__(self):super().__init__();self.current=None;self.items=[];self.ignore=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.ignore+=1
  if tag=='a' and not self.ignore:self.current={'href':dict(attrs).get('href',''),'text':[]}
 def handle_data(self,data):
  if self.current is not None and not self.ignore:self.current['text'].append(data)
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.ignore=max(0,self.ignore-1)
  if tag=='a' and self.current is not None:self.items.append(self.current);self.current=None
 def articles(self,rule,robots_text):
  seen=set();result=[]
  for row in self.items:
   url=safe_url(urljoin(rule['url'],row['href']));title=' '.join(' '.join(row['text']).split())
   if not url or url in seen or len(title)<12 or not can_fetch(rule,url,robots_text):continue
   seen.add(url);result.append({'title':title,'url':url,'source':rule['name'],'country':rule.get('country',''),'category':'GENERAL','summary':'','published':'','method':'scrape_link_fixture'})
  return result[:50]
