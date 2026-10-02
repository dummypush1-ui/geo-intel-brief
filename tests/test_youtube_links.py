import unittest
from integration.youtube_links import youtube_watch,supplied_video_watch
class YoutubeLinkTests(unittest.TestCase):
 def test_exact_bare_id(self):
  self.assertEqual(supplied_video_watch('gCNeDWCI0vo'),'https://www.youtube.com/watch?v=gCNeDWCI0vo')
  for v in [None,True,123,'gCNeDWCI0v','gCNeDWCI0voo','abcdefghij!','x\nabcdefghij','https://www.youtube.com/watch?v=gCNeDWCI0vo']:
   self.assertIsNone(supplied_video_watch(v))
 def test_exact_watch_grammar(self):
  u='https://www.youtube.com/watch?v=gCNeDWCI0vo';self.assertEqual(youtube_watch(u),u)
  for bad in [u+'&token=secret',u+'&v=abcdefghijk',u+'#x',u+'\n',u.replace('https:','http:'),u.replace('www.youtube.com','youtube.com'),u.replace('www.youtube.com','evil.com'),u.replace('www.youtube.com','user:pw@www.youtube.com'),u.replace('www.youtube.com','www.youtube.com:443'),u.replace('v=','v=%67'),u.replace('/watch?','/watch/?'),u.replace('v=','V='),u.replace('www.youtube.com','www.youtube.com.evil.com'),u.replace('www.youtube.com','www.youtube.com\\@evil.com'),None,True]:
   self.assertIsNone(youtube_watch(bad))

 def test_adapter_stream_only_and_separate_host_approval(self):
  from integration.dashboard_snapshots import DashboardSnapshots
  url='https://www.youtube.com/watch?v=gCNeDWCI0vo'
  rows=[{'name':'Video','watch_url':url}]
  def reader(key,hosts):return DashboardSnapshots({key:lambda:{'observed_at':'2026-10-02T00:00:00Z','items':rows}},True,{key:hosts})
  self.assertEqual(reader('brics_streams',['www.youtube.com']).link('brics_streams',url),url)
  self.assertIsNone(reader('brics_streams',['example.com']).link('brics_streams',url))
  for key in ['geo_events','brics_sources']:self.assertIsNone(reader(key,['www.youtube.com']).link(key,url))
  for bad in [url+'&token=x',url+'#x',url+'\n',url.replace('www.youtube.com','www.youtube.com:443')]:self.assertIsNone(reader('brics_streams',['www.youtube.com']).link('brics_streams',bad))
 def test_supplied_config_only_no_private_fields(self):
  from integration.original_dashboard_payloads import brics_video_streams
  config=[{'name':'A','country':'India','type':'video','video_id':'gCNeDWCI0vo','password':'secret','embed_url':'https://evil.com'},{'name':'B','type':'video','video_id':'https://www.youtube.com/watch?v=gCNeDWCI0vo'},{'name':'C','type':'channel','channel_id':'secret'}]
  result=brics_video_streams(config,'2026-10-02T00:00:00Z')
  self.assertEqual(len(result['items']),1);self.assertEqual(set(result['items'][0]),{'name','country','watch_url'});self.assertIn('password',config[0])
