import unittest,concurrent.futures
from integration.mail_bridge import MailSettings,ReceiptBridge,FixtureLedger
from integration.project_reports import combined_reports
class MailBridgeTests(unittest.TestCase):
 def payload(self,id='1'):return combined_reports({p:lambda p=p:{'html':'<p>'+p+' original report</p>','ids':[id]} for p in ('finder','geo','brics')})
 def bridge(self,calls):return ReceiptBridge(FixtureLedger(),{p:lambda ids,key:calls.append((ids,key)) for p in ('finder','geo','brics')},lambda r,s,h:s=='verified-send')
 def test_off_and_no_smtp(self):
  self.assertFalse(MailSettings.from_env({}).enabled)
  with self.assertRaises(ValueError):MailSettings.from_env({'MERGED_MAIL_PATH':'smtp'})
 def test_original_report_and_no_mark(self):
  calls=[];b=self.bridge(calls);d=b.prepare('r',self.payload());self.assertIn('geo original report',d['html']);self.assertEqual(calls,[])
 def test_reject_bad_proof(self):
  b=self.bridge([]);b.prepare('r',self.payload())
  for s in (False,'forged-send',''):
   with self.assertRaises(ValueError):b.acknowledge('r',s)
 def test_hash_and_copy(self):
  b=self.bridge([]);d=b.prepare('r',self.payload());d['project_ids']['geo'].append('fake');self.assertEqual(b.prepare('r',self.payload())['project_ids']['geo'],['1'])
  with self.assertRaises(ValueError):b.prepare('r',self.payload('2'))
 def test_concurrent_ack(self):
  calls=[];b=self.bridge(calls);b.prepare('r',self.payload())
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:list(e.map(lambda _:b.acknowledge('r','verified-send'),range(8)))
  self.assertEqual(len(calls),3)
 def test_partial_mark_retry(self):
  calls=[];failed=[False]
  def marker(ids,key):
   if not failed[0]:failed[0]=True;raise RuntimeError('failed')
   calls.append(key)
  b=ReceiptBridge(FixtureLedger(),{'finder':lambda ids,key:calls.append(key),'geo':marker,'brics':lambda ids,key:calls.append(key)},lambda *a:True);b.prepare('r',self.payload())
  with self.assertRaises(RuntimeError):b.acknowledge('r','send')
  b.acknowledge('r','send');self.assertEqual(calls,['r:finder','r:geo','r:brics'])
 def test_retry_reuses_stored_payload(self):
  b=self.bridge([]);first=b.prepare('r',self.payload());self.assertEqual(b.stored_payload('r'),first)
