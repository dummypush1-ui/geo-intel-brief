"""Collector109: INACTIVE bounded fetch transport contract. Injected transport
only - NO real network in this stage. Enforces https, exact allowlisted feed
URLs, decoded-byte cap, timeout cap, no redirect following, status checks.
The real RSS/XML parser sandbox is a separate gate; bytes returned here are
unparsed input for that stage, never executed.
"""
import re,math
from urllib.parse import urlsplit
class FetchRefused(ValueError):pass
MAX_BYTES=1024*1024
def _valid_feeds(feeds):
 if type(feeds)is not tuple or not 1<=len(feeds)<=64:raise FetchRefused('Exact frozen feed allowlist required')
 seen=set()
 for f in feeds:
  if type(f)is not tuple or len(f)!=3 or any(type(x)is not str for x in f):raise FetchRefused('Feed spec shape')
  name,url,cred=f
  if not 1<=len(name)<=200 or cred not in ('HIGH','MEDIUM','LOW'):raise FetchRefused('Feed name/credibility')
  if not re.fullmatch(r'https://[a-z0-9.-]+(?::\d{1,5})?/[^\s]*',url) or len(url)>2000 or url in seen:raise FetchRefused('Feed URL allowlist grammar')
  host=urlsplit(url).hostname
  if host in ('localhost',) or re.fullmatch(r'(\d+\.){3}\d+',host) or host.endswith(('.local','.internal')):raise FetchRefused('Feed host policy')
  seen.add(url)
class BoundedFetcher:
 def __init__(self,feeds,transport):
  _valid_feeds(feeds)
  if not callable(transport):raise FetchRefused('Injected transport callable required')
  self._allowed={url:(name,cred)for name,url,cred in feeds};self._t=transport
 def fetch(self,url,*,timeout=20):
  if type(url)is not str or url not in self._allowed:raise FetchRefused('URL not in reviewed allowlist')
  if type(timeout)not in (int,float) or not math.isfinite(timeout) or not 0<timeout<=30:raise FetchRefused('Timeout budget')
  name,cred=self._allowed[url]
  try:resp=self._t(url,timeout=timeout,allow_redirects=False,headers={'User-Agent':'GeoIntelMonitor/2.0'})
  except Exception:raise FetchRefused('Transport failure')from None
  try:
   status=resp.status_code;headers={str(k).lower():str(v)for k,v in dict(resp.headers).items()}
   if status in (301,302,303,307,308):raise FetchRefused('Redirect refused: re-review feed URL')
   if type(status)is not int or status!=200:raise FetchRefused('HTTP status')
   body=resp.content
   if type(body)is not bytes or len(body)>MAX_BYTES:raise FetchRefused('Decoded byte budget')
  except FetchRefused:raise
  except Exception:raise FetchRefused('Response contract')from None
  return {'source':name,'credibility':cred,'url':url,'bytes':body,'network':'injected_transport_only','parsed':False}
