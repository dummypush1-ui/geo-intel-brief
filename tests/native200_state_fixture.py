"""Stateful synthetic command fixture; no claim of Mongo isolation/durability."""
import copy
from tests.native200_wire_fixture import WireServer
from bson import BSON,Int64
import struct
class StateServer(WireServer):
 def __init__(self,data,fail=None):
  self.data=copy.deepcopy(data);self.tx={};self.tx_before={};self.fail=fail;self.failed=False;super().__init__()
 def handle(self,c):
  try:
   while not self.stop.is_set():
    header=self.exact(c,16);length,rid,_,op=struct.unpack('<iiii',header);raw=self.exact(c,length-16)
    if op==2004:pos=raw.index(b'\0',4)+9;d=BSON(raw[pos:]).decode()
    else:
     pos=4;d={}
     while pos<len(raw):
      kind=raw[pos];pos+=1;size=struct.unpack('<i',raw[pos:pos+4])[0]
      if kind==0:d.update(BSON(raw[pos:pos+size]).decode());pos+=size
      else:
       end=pos+size;pos+=4;zero=raw.index(b'\0',pos);identifier=raw[pos:zero].decode();pos=zero+1;rows=[]
       while pos<end:
        n=struct.unpack('<i',raw[pos:pos+4])[0];rows.append(BSON(raw[pos:pos+n]).decode());pos+=n
       d[identifier]=rows
    name=next(iter(d))
    with self.lock:
     self.commands.append(d);reply={'ok':1}
     if name.lower()in ('ismaster','hello'):reply.update(isWritablePrimary=True,ismaster=True,minWireVersion=0,maxWireVersion=25,logicalSessionTimeoutMinutes=30,maxBsonObjectSize=16777216,maxMessageSizeBytes=48000000,maxWriteBatchSize=100000,setName='fixture',hosts=['127.0.0.1:'+str(self.port)],primary='127.0.0.1:'+str(self.port))
     else:
      txn=repr(d.get('lsid'))+str(d.get('txnNumber'));is_tx=d.get('autocommit')is False
      if d.get('startTransaction'):self.tx[txn]=copy.deepcopy(self.data);self.tx_before[txn]=copy.deepcopy(self.data)
      db=self.tx.get(txn,self.data)if is_tx else self.data
      if name=='listCollections':
       from integration.native200_preflight import VALIDATORS
       collection=d['filter']['name'];options={'validator':VALIDATORS[collection],'validationLevel':'strict','validationAction':'error'}if collection in VALIDATORS else{};rows=[{'name':collection,'type':'collection','options':options}]if collection in self.data else[];reply['cursor']={'id':Int64(0),'ns':'geo_intel.$cmd.listCollections','firstBatch':rows}
      elif name=='listIndexes':reply['cursor']={'id':Int64(0),'ns':'geo_intel.'+d[name],'firstBatch':[{'name':'_id_','key':{'_id':1}}]}
      elif name=='find':
       rows=[copy.deepcopy(v)for v in db.get(d['find'],{}).values()if all(v.get(k)==x for k,x in d['filter'].items())];reply['cursor']={'id':Int64(0),'ns':'geo_intel.'+d['find'],'firstBatch':rows[:d['limit']]}
      elif name=='insert':
       store=db.setdefault(d['insert'],{});doc=d['documents'][0]
       if doc['_id']in store:reply.update(n=0,writeErrors=[{'code':11000,'errmsg':'duplicate','index':0}])
       else:store[doc['_id']]=copy.deepcopy(doc);reply['n']=1
      elif name=='update':
       u=d['updates'][0];store=db.get(d['update'],{});found=next((v for v in store.values()if all(v.get(k)==x for k,x in u['q'].items())),None);reply.update(n=int(found is not None),nModified=int(found is not None))
       if found is not None:store[found['_id']]=copy.deepcopy(u['u'])
      elif name=='commitTransaction':
       if txn in self.tx:
        changed=self.tx.pop(txn);before=self.tx_before.pop(txn)
        for collection,rows in changed.items():
         if rows!=before.get(collection):self.data[collection]=rows
      elif name=='abortTransaction':self.tx.pop(txn,None)
      if self.fail and not self.failed and self.fail(d):self.failed=True;reply={'ok':0,'code':391,'errmsg':'ReauthenticationRequired'}
    b=BSON.encode(reply);payload=struct.pack('<iqii',0,0,0,1)+b if op==2004 else struct.pack('<i',0)+b'\0'+b;opcode=1 if op==2004 else 2013;c.sendall(struct.pack('<iiii',16+len(payload),123,rid,opcode)+payload)
  except (EOFError,OSError):pass
  finally:
   try:c.close()
   except OSError:pass
