import unittest
from datetime import datetime,timezone
from types import SimpleNamespace
from pymongo.errors import BulkWriteError
from integration.geo_article_writer import GeoArticleWriter,WriterUnavailable
from integration.geo_collector_contract import prepare_geo_documents
R={'mapping':('geo_intel','articles'),'write_permission':True,'unique_url_index_verified':True,'source_contract_verified':True}
D=datetime(2026,1,1,tzinfo=timezone.utc)
def docs():
 return prepare_geo_documents([{'title':'Trade tariff order','url':'https://example.com','source':'Fixture','summary':'Tariff news','published':D}],['TRADE'],.85)['documents']
class Client:
 def __init__(self,error=None,result=None):self.paths=[];self.calls=[];self.error=error;self.result=result
 def __getitem__(self,k):self.paths.append(k);return self
 def insert_many(self,rows,**kw):
  self.calls.append((rows,kw))
  if self.error:raise self.error
  return self.result or SimpleNamespace(acknowledged=True,inserted_ids=['generated']*len(rows))
class Tests(unittest.TestCase):
 def test_review_gates_before_effect(self):
  for k in R:
   r=dict(R);r.pop(k);c=Client()
   with self.assertRaises(WriterUnavailable):GeoArticleWriter(c,review=r)
   self.assertEqual(c.paths,[])
 def test_original_bulk_mapping_docs_and_no_caller_mutation(self):
  d=docs();c=Client();r=GeoArticleWriter(c,review=R).write(d,D);self.assertEqual(c.paths,['geo_intel','articles']);self.assertEqual(c.calls[0][1],{'ordered':False});stored=c.calls[0][0][0];self.assertEqual(stored,dict(d[0],created_at=D.isoformat()));self.assertNotIn('emailed',stored);self.assertNotIn('created_at',d[0]);self.assertEqual(r['inserted_count'],1)
 def test_invalid_batch_before_mapping(self):
  for change in ({'_id':'x'},{'emailed':False},{'summary':'x'*301},{'telegram_url':'https://example.com'},{'published':'not-date'}):
   c=Client();d=docs();d[0].update(change)
   with self.assertRaises(WriterUnavailable) as e:GeoArticleWriter(c,review=R).write(d,D)
   self.assertIsNone(e.exception.__context__);self.assertEqual(c.paths,[]);self.assertEqual(c.calls,[])
 def test_empty_no_driver_call(self):
  c=Client();self.assertEqual(GeoArticleWriter(c,review=R).write([],D)['state'],'empty');self.assertEqual(c.paths,[])
 def test_exact_duplicate_url_vs_other_key(self):
  for key,state,duplicates,failed in ({'url':1},'duplicates',1,0),({'_id':1},'partial',0,1):
   error=BulkWriteError({'nInserted':0,'writeErrors':[{'index':0,'code':11000,'keyPattern':key}],'writeConcernErrors':[]});r=GeoArticleWriter(Client(error),review=R).write(docs(),D);self.assertEqual((r['state'],r['duplicate_count'],r['failed_count']),(state,duplicates,failed))
 def test_mixed_acknowledged_partial(self):
  e=BulkWriteError({'nInserted':1,'writeErrors':[{'index':1,'code':11000,'keyPattern':{'url':1}},{'index':2,'code':121}],'writeConcernErrors':[]});c=Client(e);d=docs()*3;r=GeoArticleWriter(c,review=R).write(d,D);self.assertEqual((r['inserted_count'],r['duplicate_count'],r['failed_count']),(1,1,1));self.assertEqual(len(c.calls),1)
 def test_network_unack_and_writeconcern_are_uncertain(self):
  for c in (Client(RuntimeError('secret-uri')),Client(result=SimpleNamespace(acknowledged=False)),Client(BulkWriteError({'nInserted':1,'writeErrors':[],'writeConcernErrors':[{'errmsg':'secret'}]}))):
   r=GeoArticleWriter(c,review=R).write(docs(),D);self.assertEqual(r['state'],'uncertain');self.assertIsNone(r['inserted_count']);self.assertNotIn('secret',str(r));self.assertFalse(r['retry_safe']);self.assertEqual(len(c.calls),1)
 def test_malformed_bulk_receipt_uncertain(self):
  for detail in ({'nInserted':0,'writeErrors':[{'index':99,'code':11000}]},{'nInserted':2,'writeErrors':[{'index':0,'code':121}]},{'nInserted':0,'writeErrors':[]}):
   self.assertEqual(GeoArticleWriter(Client(BulkWriteError(detail)),review=R).write(docs(),D)['state'],'uncertain')

 def test_mutating_driver_cannot_change_attempted_count(self):
  class Clearing(Client):
   def insert_many(self,rows,**kw):
    self.calls.append((rows,kw));rows.clear();return SimpleNamespace(acknowledged=True,inserted_ids=['id'])
  r=GeoArticleWriter(Clearing(),review=R).write(docs(),D);self.assertEqual(r['attempted'],1);self.assertEqual(r['inserted_count'],1)
 def test_snapshot_validated_before_driver_owns_copy(self):
  source=docs()
  class Mutating(Client):
   def __getitem__(self,k):
    source[0].update(_id='evil',emailed=True,title='');return super().__getitem__(k)
  c=Mutating();GeoArticleWriter(c,review=R).write(source,D);submitted=c.calls[0][0][0];self.assertNotIn('_id',submitted);self.assertNotIn('emailed',submitted);self.assertTrue(submitted['title'])
 def test_raising_details_is_uncertain_redacted(self):
  class Raising(BulkWriteError):
   def __getattribute__(self,k):
    if k=='details':raise RuntimeError('secret-details')
    return super().__getattribute__(k)
  r=GeoArticleWriter(Client(Raising({})),review=R).write(docs(),D);self.assertEqual(r['state'],'uncertain');self.assertNotIn('secret',str(r))
 def test_mapping_no_custom_equality(self):
  class Evil:
   def __eq__(self,x):raise RuntimeError('secret-equality')
  r=dict(R,mapping=Evil())
  with self.assertRaises(WriterUnavailable):GeoArticleWriter(Client(),review=r)
 def test_noninteger_pattern_not_confirmed_duplicate(self):
  for v in (True,1.0):
   e=BulkWriteError({'nInserted':0,'writeErrors':[{'index':0,'code':11000,'keyPattern':{'url':v}}],'writeConcernErrors':[]});r=GeoArticleWriter(Client(e),review=R).write(docs(),D);self.assertEqual(r['state'],'uncertain');self.assertIsNone(r['duplicate_count'])

 def test_bulk_error_receipt_not_command_duplicate(self):
  class Receipt:
   @property
   def acknowledged(self):raise BulkWriteError({'nInserted':0,'writeErrors':[{'index':0,'code':11000,'keyPattern':{'url':1}}],'writeConcernErrors':[]})
  r=GeoArticleWriter(Client(result=Receipt()),review=R).write(docs(),D);self.assertEqual(r['state'],'uncertain');self.assertIsNone(r['duplicate_count'])
 def test_receipt_attributes_read_once(self):
  class Receipt:
   def __init__(self):self.acks=0;self.ids=0
   @property
   def acknowledged(self):self.acks+=1;return True
   @property
   def inserted_ids(self):self.ids+=1;return ['id'] if self.ids==1 else object()
  receipt=Receipt();r=GeoArticleWriter(Client(result=receipt),review=R).write(docs(),D);self.assertEqual(r['state'],'inserted');self.assertEqual((receipt.acks,receipt.ids),(1,1))
 def test_concern_exact_list_required(self):
  class Equal:
   def __eq__(self,v):return True
  for concern in (Equal(),None,(),False):
   e=BulkWriteError({'nInserted':0,'writeErrors':[{'index':0,'code':11000,'keyPattern':{'url':1}}],'writeConcernErrors':concern});self.assertEqual(GeoArticleWriter(Client(e),review=R).write(docs(),D)['state'],'uncertain')
 def test_review_str_subclass_keys_rejected(self):
  class S(str):pass
  r={S(k):v for k,v in R.items()}
  with self.assertRaises(WriterUnavailable):GeoArticleWriter(Client(),review=r)

 def test_lookup_bulk_error_not_insert_duplicate(self):
  class Lookup(Client):
   def __getitem__(self,k):raise BulkWriteError({'nInserted':0,'writeErrors':[{'index':0,'code':11000,'keyPattern':{'url':1}}],'writeConcernErrors':[]})
  c=Lookup();r=GeoArticleWriter(c,review=R).write(docs(),D);self.assertEqual(r['state'],'uncertain');self.assertEqual(c.calls,[])
 def test_method_binding_bulk_error_not_insert_duplicate(self):
  class Lookup(Client):
   @property
   def insert_many(self):raise BulkWriteError({'nInserted':0,'writeErrors':[{'index':0,'code':11000,'keyPattern':{'url':1}}],'writeConcernErrors':[]})
  c=Lookup();r=GeoArticleWriter(c,review=R).write(docs(),D);self.assertEqual(r['state'],'uncertain');self.assertEqual(c.calls,[])
 def test_keypattern_hooks_not_called_and_counts_coherent(self):
  hooks=[];errors=[]
  class S(str):
   __hash__=str.__hash__
   def __eq__(self,v):hooks.append(v);errors.clear();return str.__eq__(self,v)
  errors.extend([{'index':0,'code':11000,'keyPattern':{S('url'):1}},{'index':1,'code':121}])
  e=BulkWriteError({'nInserted':0,'writeErrors':errors,'writeConcernErrors':[]});r=GeoArticleWriter(Client(e),review=R).write(docs()*2,D);self.assertEqual(hooks,[]);self.assertEqual(r['state'],'uncertain');self.assertEqual(r['uncertain_count'],2)

 def test_shared_nested_input_node_budget(self):
  source=docs()[0];shared=[None]*1000;source['extra']=[shared]*1000;c=Client()
  with self.assertRaises(WriterUnavailable):GeoArticleWriter(c,review=R).write([source],D)
  self.assertEqual(c.paths,[])
 def test_score_integer_bson_safe_bounds(self):
  for score in (2**53+1,-2**53-1,2**100):
   source=docs();source[0]['score']=score;c=Client()
   with self.assertRaises(WriterUnavailable):GeoArticleWriter(c,review=R).write(source,D)
   self.assertEqual(c.paths,[])
