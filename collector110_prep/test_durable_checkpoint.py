import unittest,copy,threading
from types import SimpleNamespace
from datetime import datetime,timezone
from .input_budget import capture
from .durable_checkpoint import DurableCheckpoints,DurableCheckpointRefused
class Collection:
 def __init__(self):
  self.rows={};self.lock=threading.Lock();self.write_concern=SimpleNamespace(document={'w':'majority','j':True,'wtimeout':5000});self.read_concern=SimpleNamespace(document={'level':'majority'})
 def update_one(self,q,u,upsert=False):
  with self.lock:self.rows.setdefault(q['_id'],copy.deepcopy(u['$setOnInsert']))
  return SimpleNamespace(acknowledged=True)
 def find_one(self,q):return copy.deepcopy(self.rows.get(q['_id']))
def inputs():return {'candidates':[{'published':datetime(2026,1,1,tzinfo=timezone.utc),'title':'x'}],'active_categories':['TRADE'],'threshold':.85}
class Tests(unittest.TestCase):
 def setUp(self):self.c=Collection();self.s=DurableCheckpoints(self.c);self.key='a'*64
 def test_reinstantiation_roundtrip(self):
  h=self.s.put(self.key,1,inputs());other=DurableCheckpoints(self.c)
  self.assertEqual(other.get(self.key,1),inputs());self.assertEqual(h,self.s.put(self.key,1,inputs()))
 def test_mismatch_never_replaces(self):
  self.s.put(self.key,1,inputs());original=copy.deepcopy(self.c.rows)
  v=inputs();v['threshold']=.8
  with self.assertRaises(DurableCheckpointRefused):self.s.put(self.key,1,v)
  with self.assertRaises(DurableCheckpointRefused):self.s.get(self.key,2)
  self.assertEqual(self.c.rows,original)
 def test_mutation_is_detected(self):
  self.s.put(self.key,1,inputs());self.c.rows[self.key]['hash']='0'*64
  with self.assertRaises(DurableCheckpointRefused):self.s.get(self.key,1)
 def test_concern_contract(self):
  for wc in ({'w':1,'j':True,'wtimeout':5000},{'w':'majority','j':False,'wtimeout':5000},{'w':'majority','j':True,'wtimeout':True}):
   self.c.write_concern.document=wc
   with self.assertRaises(DurableCheckpointRefused):DurableCheckpoints(self.c)
 def test_unacknowledged_never_success(self):
  self.c.update_one=lambda *a,**k:SimpleNamespace(acknowledged=False)
  with self.assertRaises(DurableCheckpointRefused):self.s.put(self.key,1,inputs())
 def test_readback_failure_blocks(self):
  self.c.find_one=lambda *a:None
  with self.assertRaises(DurableCheckpointRefused):self.s.put(self.key,1,inputs())
 def test_parallel_different_inputs_one_winner(self):
  out=[]
  def run(threshold):
   b=inputs();b['threshold']=threshold
   try:out.append(self.s.put(self.key,1,b))
   except DurableCheckpointRefused:out.append(None)
  ts=[threading.Thread(target=run,args=(t,))for t in (.85,.8)]
  for t in ts:t.start()
  for t in ts:t.join()
  self.assertEqual(sum(x is not None for x in out),1)
 def test_encoded_input_depth_refuses(self):
  self.s.put(self.key,1,inputs());v=[]
  for _ in range(30):v=[v]
  self.c.rows[self.key]['inputs']=v
  with self.assertRaises(DurableCheckpointRefused):self.s.get(self.key,1)
 def test_real_bson_boundary_roundtrip(self):
  from bson import BSON
  for n in (-(2**63),2**63-1):
   self.setUp();b=inputs();b['candidates'][0]['n']=n
   self.s.put(self.key,1,b)
   encoded=BSON.encode(self.c.rows[self.key])
   self.c.rows[self.key]=BSON(encoded).decode()
   self.assertEqual(self.s.get(self.key,1)['candidates'][0]['n'],n)
 def test_int64_one_beyond_before_store(self):
  for n in (-(2**63)-1,2**63,2**64-1):
   self.setUp();b=inputs();b['candidates'][0]['n']=n
   with self.assertRaises(DurableCheckpointRefused):self.s.put(self.key,1,b)
   self.assertEqual(self.c.rows,{})

 def test_invalid_integer_wire_encodings(self):
  from .durable_checkpoint import _decode
  for raw in ('01','-0','+1','1.0','9223372036854775808','-9223372036854775809',True,1):
   with self.assertRaises(DurableCheckpointRefused):_decode(['int',raw])

if __name__=='__main__':unittest.main(verbosity=2)
