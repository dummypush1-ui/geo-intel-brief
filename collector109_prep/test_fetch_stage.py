import unittest,sys
from .fetch_stage import BoundedFetcher,FetchRefused,MAX_BYTES
FEEDS=(('A','https://a.example/rss','HIGH'),('B','https://b.example/feed','MEDIUM'))
class Resp:
 def __init__(self,s,b,h=None):self.status_code=s;self.content=b;self.headers=h or {}
class Tests(unittest.TestCase):
 def test_allowlist_enforced(self):
  f=BoundedFetcher(FEEDS,lambda u,**k:Resp(200,b'x'))
  for bad in ('https://evil.example/x','http://a.example/rss','https://a.example/rss/../x','a.example/rss'):
   with self.assertRaises(FetchRefused):f.fetch(bad)
 def test_success_contract(self):
  out=BoundedFetcher(FEEDS,lambda u,**k:Resp(200,b'<rss/>')).fetch('https://b.example/feed')
  self.assertEqual(out['credibility'],'MEDIUM');self.assertFalse(out['parsed'])
 def test_redirect_refused(self):
  f=BoundedFetcher(FEEDS,lambda u,**k:Resp(302,b'',{'Location':'https://a.example/rss'}))
  with self.assertRaises(FetchRefused):f.fetch('https://a.example/rss')
 def test_status_and_transport_failure(self):
  for t in (lambda u,**k:Resp(500,b''),lambda u,**k:(_ for _ in ()).throw(RuntimeError())):
   with self.assertRaises(FetchRefused):BoundedFetcher(FEEDS,t).fetch('https://a.example/rss')
 def test_byte_budget_and_timeout(self):
  with self.assertRaises(FetchRefused):BoundedFetcher(FEEDS,lambda u,**k:Resp(200,b'x'*(MAX_BYTES+1))).fetch('https://a.example/rss')
  with self.assertRaises(FetchRefused):BoundedFetcher(FEEDS,lambda u,**k:Resp(200,b'')).fetch('https://a.example/rss',timeout=60)
 def test_feed_allowlist_validation(self):
  for bad in ((('A','http://a.example/x','HIGH'),),(('A','https://127.0.0.1/x','HIGH'),),(('A','https://a.example/x','high'),),'notuple'):
   with self.assertRaises(FetchRefused):BoundedFetcher(bad,lambda u,**k:Resp(200,b''))
if __name__=='__main__':unittest.main(verbosity=2)
