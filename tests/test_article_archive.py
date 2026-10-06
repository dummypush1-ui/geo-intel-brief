import unittest,json,hashlib,copy
from datetime import datetime,timezone,timedelta
from bson import ObjectId
from integration.article_archive import pack,unpack,retrieve,ArchiveRefused,encode,decode
STAMP='2026-10-06T00:00:00Z'
class Tests(unittest.TestCase):
 def test_exact_typed_roundtrip_and_order(self):
  rows=[{'_id':ObjectId('000000000000000000000001'),'title':'தமிழ்\nline','summary':'x'*10000,'score':-2**53,'emailed':False,'telegram_message_id':-2**63,'created_at':'2026-10-06T05:30:00+05:30','published':'2026-10-06T00:00:00Z'},{'_id':'000000000000000000000001','summary':'bytes text','score':1.0}]
  data=pack(rows,created_at=STAMP);out=unpack(data);self.assertEqual(out['rows'],rows);self.assertEqual(list(out['rows'][0]),list(rows[0]));self.assertIs(type(out['rows'][0]['emailed']),bool);self.assertIs(type(out['rows'][1]['score']),float);self.assertFalse(out['receipt']['durable_backup']);self.assertEqual(retrieve(data,rows[0]['_id'])['record'],rows[0])
 def test_null_missing_taglike_values(self):
  self.assertEqual(decode(encode(-2**63)),-2**63);self.assertEqual(decode(encode(2**63-1)),2**63-1)
  literal={'__tag__':'oid','value':['oid','literal'], 'null':None,'bytes':b'bytes'};self.assertEqual(decode(encode(literal)),literal)
  rows=[{'_id':'id','title':'literal','telegram_message_id':None}];self.assertEqual(unpack(pack(rows,created_at=STAMP))['rows'],rows)
  self.assertNotIn('published',unpack(pack(rows,created_at=STAMP))['rows'][0])
 def test_duplicate_identity_policy_and_ambiguous_lookup(self):
  r={'_id':'id','summary':'same'};data=pack([r,r],created_at=STAMP);self.assertEqual(len(unpack(data)['rows']),2)
  with self.assertRaises(ArchiveRefused):retrieve(data,'id')
  with self.assertRaises(ArchiveRefused):pack([r,dict(r,summary='different')],created_at=STAMP)
 def test_empty_truncated_aliasing(self):
  self.assertEqual(unpack(pack([],created_at=STAMP))['rows'],[]);r={'_id':'id','summary':'a'};data=pack([r],created_at=STAMP,scope='supplied_truncated_subset');r['summary']='changed';out=unpack(data);self.assertEqual(out['rows'][0]['summary'],'a');out['rows'][0]['summary']='tamper';self.assertEqual(retrieve(data,'id')['record']['summary'],'a')
 def test_types_bounds_private(self):
  for value in [float('nan'),float('inf'),2**63,-2**63-1,object(),datetime(2026,10,6,0,0,0,1,tzinfo=timezone.utc)]:
   with self.assertRaises(ArchiveRefused):pack([{'_id':'id','summary':value}],created_at=STAMP)
  for k in ['body','raw_text','password','session','MongoDB_URI','api_key']:
   with self.assertRaises(ArchiveRefused):pack([{'_id':'id',k:'secret'}],created_at=STAMP)
  with self.assertRaises(ArchiveRefused):pack([{'_id':'id','summary':'x'*1000001}],created_at=STAMP)
 def test_bson_datetime_normalization_and_boundaries(self):
  d=datetime(2026,10,6,5,30,tzinfo=timezone(timedelta(hours=5,minutes=30)));v=decode(encode(d));self.assertEqual(v,d);self.assertEqual(v.tzinfo,timezone.utc)
  for stamp in ['1970-01-01T00:00:00+01:00','2100-12-31T23:30:00-01:00']:
   with self.assertRaises(ArchiveRefused):pack([],created_at=stamp)
 def test_corruption_manifest_version_digest_duplicate_json(self):
  data=pack([{'_id':'id','title':'safe'}],created_at=STAMP)
  for mutate in [lambda b:b.update(version=True),lambda b:b.update(count=2),lambda b:b['manifest'].update(supported_fields=[]),lambda b:b.update(scope='full_db_history'),lambda b:b['records'][0].append('extra')]:
   obj=json.loads(data);mutate(obj['body']);obj['sha256']=hashlib.sha256(json.dumps(obj['body'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
   with self.assertRaises(ArchiveRefused):unpack(json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode())
  with self.assertRaises(ArchiveRefused):unpack(data.replace(b'"safe"',b'"bad"'))
  with self.assertRaises(ArchiveRefused):unpack(b'{"body":{},"body":{},"sha256":"x"}')
  with self.assertRaises(ArchiveRefused):unpack(b'x'*(2*1024*1024+1))
 def test_scalar_subclasses_no_hooks(self):
  class Evil(str):
   def __str__(self):raise AssertionError('hook')
  with self.assertRaises(ArchiveRefused):pack([{'_id':'id','title':Evil('bad')}],created_at=STAMP)

 def test_nested_private_fields_and_aggregate_capture_budget(self):
  for field in ['title','summary','source','emailed','published']:
   with self.assertRaises(ArchiveRefused):pack([{'_id':'id',field:{'password':'secret','MongoDB_URI':'mongodb://private'}}],created_at=STAMP)
  with self.assertRaises(ArchiveRefused):pack([{'_id':str(i),'summary':'x'*500000} for i in range(100)],created_at=STAMP)
  with self.assertRaises(ArchiveRefused):pack([{'_id':str(i),'summary':'界'*100000} for i in range(100)],created_at=STAMP)

 def test_budget_stops_before_next_record_and_tagcopy(self):
  from unittest.mock import patch
  with patch('integration.article_archive.encode',side_effect=AssertionError('overrun must stop before tagged copy')):
   with self.assertRaises(ArchiveRefused):pack([{'_id':'id','summary':'x'*500000}],created_at=STAMP)
  class Unvisited(dict):pass
  with self.assertRaises(ArchiveRefused):pack([{'_id':str(i),'title':'界'*100000} for i in range(10)]+[Unvisited()],created_at=STAMP)
