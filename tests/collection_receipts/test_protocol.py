import unittest
from integration.collection_receipts.protocol import *
class ProtocolTests(unittest.TestCase):
 def setUp(self):
  self.full={'url':'https://example.org/a','summary':'🙂'*5000};self.plan=plan_pieces(self.full)
  self.j=journal_new('outbox',1,'attempt','verified-channel',self.plan)
 def test_lossless_fulltext_and_utf16(self):
  self.assertEqual(json.loads(''.join(p['text'] for p in self.plan['pieces'])),self.full)
  self.assertTrue(all(len(p['text'].encode('utf-16-le'))//2<=3000 for p in self.plan['pieces']))
 def test_restart_unknown_no_resend(self):
  j=recover(start_piece(self.j,0));self.assertEqual(j['state'],'unknown')
  with self.assertRaises(ReceiptRefused):start_piece(j,0)
  self.assertFalse(publishable(j))
 def test_allpiece_ack_only(self):
  j=self.j
  for i,p in enumerate(self.plan['pieces']):
   self.assertFalse(publishable(j));j=record_ack(start_piece(j,i),attempt_id='attempt',destination='verified-channel',index=i,piece_sha256=p['sha256'],provider_message_id=i+1)
  self.assertTrue(publishable(j))
  with self.assertRaises(ReceiptRefused):start_piece(j,0)
 def test_stale_attempt_or_destination(self):
  j=start_piece(self.j,0)
  for kw in ({'attempt_id':'stale'},{'destination':'other'},{'piece_sha256':'a'*64}):
   args=dict(attempt_id='attempt',destination='verified-channel',index=0,piece_sha256=self.plan['pieces'][0]['sha256'],provider_message_id=1);args.update(kw)
   with self.assertRaises(ReceiptRefused):record_ack(j,**args)
 def test_exact_commit_identity(self):
  b=[{'url':self.full['url'],'record_sha256':self.plan['record_sha256']}]
  r=[dict(b[0],state='newly_committed',article_id='a',full_record_id='f',outbox_id='o',version=1)]
  self.assertEqual(validate_commit(b,r),r)
  for bad in (1,[],[dict(r[0],record_sha256='b'*64)],[dict(r[0],state='unknown')]):
   with self.assertRaises(ReceiptRefused):validate_commit(b,bad)
 def test_partial_commits_explicit_not_inferred(self):
  b=[{'url':'https://example.org/'+str(i),'record_sha256':digest({'i':i})} for i in range(3)]
  r=[dict(b[0],state='newly_committed',article_id='a',full_record_id='f',outbox_id='o',version=1),dict(b[1],state='unknown'),dict(b[2],state='rejected')]
  self.assertEqual([x['state'] for x in validate_commit(b,r)],['newly_committed','unknown','rejected'])
 def test_duplicate_receipt_refused(self):
  b=[{'url':'a','record_sha256':digest(1)},{'url':'b','record_sha256':digest(2)}]
  with self.assertRaises(ReceiptRefused):validate_commit(b,[dict(b[0],state='unknown')]*2)
 def test_unhashable_receipt_url(self):
  b=[{'url':'a','record_sha256':digest(1)}]
  with self.assertRaises(ReceiptRefused):validate_commit(b,[{'url':[], 'record_sha256':digest(1),'state':'unknown'}])
 def test_nonunicode_and_nan_refused(self):
  for value in ({'summary':'\ud800'},{'score':float('nan')}):
   with self.assertRaises(ReceiptRefused):plan_pieces(value)
if __name__=='__main__':unittest.main()
