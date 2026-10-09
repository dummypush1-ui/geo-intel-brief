"""Disposable loopback Mongo wire fixture, not an actual Mongo durability server."""
import socket,threading,struct
from bson import BSON,Int64
class WireServer:
 def __init__(self,commit_reply=None,mode='ok',hello_mode='replica'):
  self.sock=socket.socket();self.sock.bind(('127.0.0.1',0));self.sock.listen();self.sock.settimeout(.1);self.port=self.sock.getsockname()[1];self.stop=threading.Event();self.commands=[];self.lock=threading.Lock();self.connections=[];self.threads=[];self.mode=mode;self.commit_reply=commit_reply;self.hello_mode=hello_mode
  self.t=threading.Thread(target=self.accept,daemon=True);self.t.start()
 def accept(self):
  while not self.stop.is_set():
   try:c,_=self.sock.accept()
   except socket.timeout:continue
   except OSError:return
   self.connections.append(c);t=threading.Thread(target=self.handle,args=(c,),daemon=True);self.threads.append(t);t.start()
 def exact(self,c,n):
  out=b''
  while len(out)<n:
   b=c.recv(n-len(out))
   if not b:raise EOFError()
   out+=b
  return out
 def handle(self,c):
  try:
   while not self.stop.is_set():
    header=self.exact(c,16);length,rid,_,op=struct.unpack('<iiii',header);raw=self.exact(c,length-16)
    if op==2004:
     pos=raw.index(b'\0',4)+1+8;d=BSON(raw[pos:]).decode()
    elif op==2013:
     assert raw[4]==0;size=struct.unpack('<i',raw[5:9])[0];d=BSON(raw[5:5+size]).decode()
    else:raise ValueError(op)
    name=next(iter(d))
    with self.lock:self.commands.append(d)
    if name.lower()in ('ismaster','hello'):
     reply={'ok':1,'isWritablePrimary':True,'ismaster':True,'minWireVersion':0,'maxWireVersion':25,'logicalSessionTimeoutMinutes':30,'maxBsonObjectSize':16777216,'maxMessageSizeBytes':48000000,'maxWriteBatchSize':100000}
     if self.hello_mode=='replica':reply.update(setName='fixture',hosts=['127.0.0.1:'+str(self.port)],primary='127.0.0.1:'+str(self.port))
     elif self.hello_mode=='mongos':reply['msg']='isdbgrid'
    elif name=='find':reply={'ok':1,'cursor':{'id':Int64(0),'ns':'geo_intel.fixture','firstBatch':[]}}
    elif name in ('commitTransaction','abortTransaction'):
     if self.mode=='drop':c.close();return
     reply=self.commit_reply or {'ok':1}
    else:reply={'ok':1}
    b=BSON.encode(reply)
    payload=struct.pack('<iqii',0,0,0,1)+b if op==2004 else struct.pack('<i',0)+b'\0'+b
    opcode=1 if op==2004 else 2013;c.sendall(struct.pack('<iiii',16+len(payload),123,rid,opcode)+payload)
  except (EOFError,OSError):pass
  finally:
   try:c.close()
   except OSError:pass
 def close(self):
  self.stop.set();self.sock.close()
  for c in self.connections:
   try:c.shutdown(socket.SHUT_RDWR);c.close()
   except OSError:pass
  self.t.join(1)
  for t in self.threads:t.join(1)
