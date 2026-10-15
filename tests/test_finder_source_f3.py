import copy,hashlib,json,unittest
from unittest.mock import Mock,patch
from integration import finder_source_f3 as m
ENV={m.FLAG:'true',m.reconcile.FLAG:'true',m.reconcile.build.FLAG:'true'}
REV='a'*40;TOP='b'*40;SRC='c'*40
class Tests(unittest.TestCase):
 def records(self):
  raw={'tradepartners.ts':b'synthetic partners','sanctions.ts':b'synthetic sanctions'}
  blobs=[{'path':n,'mode':'100644','type':'blob','size':len(b),'sha':hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()}for n,b in raw.items()]
  return {m.API+'commits/'+REV:{'sha':REV,'tree':{'sha':TOP}},m.API+'trees/'+TOP:{'sha':TOP,'truncated':False,'tree':[{'path':'src','mode':'040000','type':'tree','sha':SRC}]},m.API+'trees/'+SRC:{'sha':SRC,'truncated':False,'tree':blobs},**{m.RAW+REV+'/src/'+n:b for n,b in raw.items()}}
 def fetcher(self,records,seen):
  def fetch(url,limit,timeout):
   seen.append((url,limit,timeout));value=records[url];return value if type(value)is bytes else json.dumps(value).encode()
  return fetch
 def test_off_before_fetch_and_closed_flags(self):
  fetch=lambda *a:(_ for _ in()).throw(AssertionError())
  self.assertEqual(m.prepare({},fetch=fetch)['state'],'disabled');self.assertIsNone(m.acquire({},fetch=fetch))
  for env in ({m.FLAG:'true'},{m.FLAG:'TRUE'},{m.FLAG:'true',m.reconcile.FLAG:'true'}):
   with self.assertRaises((m.Held,m.reconcile.Held)):m.acquire(env,revision=REV,fetch=fetch)
  for rev in ('main','../main','A'*40,'a'*39,None):
   with self.assertRaises(m.Held):m.acquire(ENV,revision=rev,fetch=fetch)
 def test_exact_five_reads_blob_binding_and_no_secrets(self):
  seen=[];out=m.acquire(ENV,revision=REV,fetch=self.fetcher(self.records(),seen),clock=lambda:0)
  self.assertEqual(len(seen),5);self.assertEqual(out['evidence']['requests'],5);self.assertFalse(out['evidence']['credentials_sent']);self.assertFalse(out['evidence']['official_freshness_verified'])
  self.assertTrue(all(0<x[2]<=20 for x in seen));self.assertEqual({r['path']for r in out['snapshot']['source_files']},set(m.reconcile.FILES))
 def test_commit_tree_mode_size_duplicate_and_blob_fail_closed(self):
  mutations=[lambda r:r[m.API+'commits/'+REV].update(sha='d'*40),lambda r:r[m.API+'commits/'+REV].update(tree={'sha':'../bad'}),lambda r:r[m.API+'trees/'+TOP].update(truncated=True),lambda r:r[m.API+'trees/'+TOP]['tree'][0].update(mode='120000'),lambda r:r[m.API+'trees/'+SRC]['tree'][0].update(mode='100755'),lambda r:r[m.API+'trees/'+SRC]['tree'][0].update(size=True),lambda r:r[m.API+'trees/'+SRC]['tree'][0].update(size=m.MAX_FILE+1),lambda r:r[m.API+'trees/'+SRC]['tree'].append(copy.deepcopy(r[m.API+'trees/'+SRC]['tree'][0])),lambda r:r.update({m.RAW+REV+'/src/sanctions.ts':b'changed'})]
  for mutation in mutations:
   records=self.records();mutation(records);seen=[]
   with self.subTest(mutation=mutation),self.assertRaises(m.Held):m.acquire(ENV,revision=REV,fetch=self.fetcher(records,seen),clock=lambda:0)
   self.assertLessEqual(len(seen),5)
 def test_failure_no_retry_caps_and_deadline(self):
  seen=[]
  def failed(*args):seen.append(args);raise OSError('secret diagnostic never forwarded')
  with self.assertRaisesRegex(m.Held,'last-good'):m.acquire(ENV,revision=REV,fetch=failed)
  self.assertEqual(len(seen),1)
  for raw in ('not bytes',b'x'*(m.MAX_JSON+1),b'{"sha":"a","sha":"b"}'):
   with self.assertRaises(m.Held):m.acquire(ENV,revision=REV,fetch=lambda *a:raw,clock=lambda:0)
  times=iter([0,91])
  with self.assertRaisesRegex(m.Held,'timeout'):m.acquire(ENV,revision=REV,fetch=failed,clock=lambda:next(times))
  seen=[];times=iter([0,0,91])
  with self.assertRaisesRegex(m.Held,'timeout'):m.acquire(ENV,revision=REV,fetch=self.fetcher(self.records(),seen),clock=lambda:next(times))
  self.assertEqual(len(seen),1)
 def test_bound_snapshot_delivered_only_to_reconciliation(self):
  seen=[]
  with patch.object(m.reconcile,'prepare',return_value={'state':'held'})as prepare:
   result=m.prepare(ENV,revision=REV,fetch=self.fetcher(self.records(),seen),clock=lambda:0)
  snapshot=prepare.call_args.kwargs['snapshot'];self.assertEqual(snapshot['revision'],REV);self.assertEqual(result['state'],'held_source_and_consumer_review_required');self.assertFalse(result['writes']);self.assertFalse(result['published'])
 def test_redirect_blocked(self):
  with self.assertRaisesRegex(m.Held,'redirect'):m.NoRedirect().redirect_request(None,None,None,None,None,None)
class ReviewNits(Tests):
 def test_blob_sha_size_and_entry_range_independently(self):
  mutations=[lambda r:r[m.API+'trees/'+SRC]['tree'][0].update(sha='e'*40),lambda r:r[m.API+'trees/'+SRC]['tree'][0].update(size=1),lambda r:r[m.API+'trees/'+SRC]['tree'][0].update(size=0),lambda r:r[m.API+'trees/'+SRC]['tree'][0].update(size=-1),lambda r:r[m.API+'trees/'+SRC]['tree'][0].update(size=m.MAX_FILE+1)]
  for mutation in mutations:
   records=self.records();mutation(records)
   with self.assertRaises(m.Held):m.acquire(ENV,revision=REV,fetch=self.fetcher(records,[]),clock=lambda:0)
 def test_download_opener_proxy_status_url_headers_and_read_caps(self):
  class Response:
   status=200
   headers={}
   def geturl(self):return m.API+'commits/'+REV
   def read(self,n):self.n=n;return b'{}'
   def __enter__(self):return self
   def __exit__(self,*args):pass
  response=Response();opener=Mock();opener.open.return_value=response
  with patch.object(m.urllib.request,'build_opener',return_value=opener)as build:
   self.assertEqual(m.download(m.API+'commits/'+REV,10,2),b'{}')
   handlers=build.call_args.args;self.assertIsInstance(handlers[0],m.urllib.request.ProxyHandler);self.assertEqual(handlers[0].proxies,{});self.assertIsInstance(handlers[1],m.NoRedirect);self.assertEqual(response.n,11)
   request=opener.open.call_args.args[0];self.assertNotIn('Authorization',request.headers);self.assertNotIn('Cookie',request.headers)
   response.status=403
   with self.assertRaises(m.Held):m.download(m.API+'commits/'+REV,10,2)
   response.status=200;response.geturl=lambda:'https://evil.invalid'
   with self.assertRaises(m.Held):m.download(m.API+'commits/'+REV,10,2)
   response.geturl=lambda:m.API+'commits/'+REV
   for headers in ({'Content-Length':'11'},{'Content-Length':'bad'},{'Content-Encoding':'gzip'}):
    response.headers=headers
    with self.assertRaises(m.Held):m.download(m.API+'commits/'+REV,10,2)
   response.headers={};response.read=lambda n:b'x'*11
   with self.assertRaises(m.Held):m.download(m.API+'commits/'+REV,10,2)
   # A misbehaving opener that ignores read(n) also hits the post-read cap.
   response.read=lambda n:b'x'*100
   with self.assertRaises(m.Held):m.download(m.API+'commits/'+REV,10,2)
 def test_get_contract_and_postresponse_timeout_directly(self):
  for value in ('wrong type',b'x'*(m.MAX_JSON+1)):
   with self.assertRaisesRegex(m.Held,'byte contract'):m.acquire(ENV,revision=REV,fetch=lambda *a:value,clock=lambda:0)
  times=iter([0,0,91]);seen=[]
  with self.assertRaisesRegex(m.Held,'total timeout'):m.acquire(ENV,revision=REV,fetch=self.fetcher(self.records(),seen),clock=lambda:next(times))
  self.assertEqual(len(seen),1)
 def test_tree_sha_and_entry_cap(self):
  for mode in ('sha','cap'):
   records=self.records()
   if mode=='sha':records[m.API+'trees/'+SRC]['sha']='d'*40
   else:records[m.API+'trees/'+SRC]['tree']=[{'path':str(i)}for i in range(20001)]
   with self.assertRaisesRegex(m.Held,'Complete exact source tree'):m.acquire(ENV,revision=REV,fetch=self.fetcher(records,[]),clock=lambda:0)
 def test_redirect_evidence_explicit(self):
  out=m.acquire(ENV,revision=REV,fetch=self.fetcher(self.records(),[]),clock=lambda:0);self.assertEqual(out['evidence']['redirects'],0)
if __name__=='__main__':unittest.main()
