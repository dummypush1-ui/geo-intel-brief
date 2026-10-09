"""Read-only loopback responder. No write command implementation."""
import copy,struct
from bson import BSON,Int64
from tests.native200_wire_fixture import WireServer
from integration.native200_admission_preflight import VALIDATORS
class ReadServer(WireServer):
 def __init__(self,data,fail=None):
  self.data=copy.deepcopy(data);self.fail=fail;super().__init__()
 def handle(self,c):
  try:
   while not self.stop.is_set():
    header=self.exact(c,16);length,rid,_,op=struct.unpack('<iiii',header);raw=self.exact(c,length-16)
    if op==2004:pos=raw.index(b'\0',4)+9;d=BSON(raw[pos:]).decode()
    else:assert raw[4]==0;size=struct.unpack('<i',raw[5:9])[0];d=BSON(raw[5:5+size]).decode()
    name=next(iter(d))
    with self.lock:self.commands.append(d)
    if name.lower()in ('ismaster','hello'):
     reply={'ok':1,'isWritablePrimary':True,'ismaster':True,'minWireVersion':0,'maxWireVersion':25,'logicalSessionTimeoutMinutes':30,'maxBsonObjectSize':16777216,'maxMessageSizeBytes':48000000,'maxWriteBatchSize':100000,'setName':'fixture','hosts':['127.0.0.1:'+str(self.port)],'primary':'127.0.0.1:'+str(self.port)}
    elif name=='buildInfo':reply={'ok':1,'version':'8.0.1'}
    elif name=='count':reply={'ok':1,'n':len(self.data[d[name]])}
    elif name in ('listCollections','listIndexes','find'):
     if name=='listCollections':
      n=d['filter']['name'];rows=[{'name':n,'type':'collection','options':{'validator':VALIDATORS[n],'validationLevel':'strict','validationAction':'error'}}];ns='geo_intel.$cmd.listCollections'
     elif name=='listIndexes':rows=[{'name':'_id_','key':{'_id':1}}];ns='geo_intel.'+d[name]
     else:rows=list(self.data[d[name]].values());ns='geo_intel.'+d[name]
     reply={'ok':1,'cursor':{'id':Int64(0),'ns':ns,'firstBatch':rows}}
    else:reply={'ok':0,'code':13,'errmsg':'Read-only fixture refuses this command'}
    if self.fail and self.fail(d):reply={'ok':0,'code':391,'errmsg':'ReauthenticationRequired'}
    b=BSON.encode(reply);payload=struct.pack('<iqii',0,0,0,1)+b if op==2004 else struct.pack('<i',0)+b'\0'+b;opcode=1 if op==2004 else 2013;c.sendall(struct.pack('<iiii',16+len(payload),123,rid,opcode)+payload)
  except (EOFError,OSError):pass
  finally:
   try:c.close()
   except OSError:pass
