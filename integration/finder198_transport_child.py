"""Fixed secret-in-pipe transport child. No retries/redirects/logs/ambient env.
Parent owns20s hard wall bound incl DNS. Only closed sanitized response protocol.
"""
import sys,os,json,time,socket,ssl,http.client,ipaddress,base64,resource
from pathlib import Path
if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(256*1024*1024,256*1024*1024))
 resource.setrlimit(resource.RLIMIT_NOFILE,(32,32))
 resource.setrlimit(resource.RLIMIT_FSIZE,(2097152,2097152))
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from integration.finder198_connector import FIXED_BASE,MAX_REQUEST_BYTES,MAX_RESPONSE_BYTES,PORTS
HOST='hsn-ai-proxy.onrender.com'
def perform(path,method,body,secret,*,deadline):
 if method not in ('GET','POST')or type(path)is not str or len(path)>200 or not path.startswith('/')or any(c in path for c in ('\r','\n','#','\\',' '))or type(body)is not bytes or len(body)>MAX_REQUEST_BYTES or type(secret)is not str or not 48<=len(secret)<=256 or any(not 33<=ord(c)<=126 for c in secret):raise ValueError()
 if method=='GET':
  if not path.startswith('/ships?port=')or path.removeprefix('/ships?port=')not in PORTS|{'ALL'}or body:raise ValueError()
 else:
  import re
  if path not in ('/groq/openai/v1/chat/completions','/mistral/v1/chat/completions')and not re.fullmatch(r'/gemini/v1beta/models/[A-Za-z0-9._-]+:generateContent',path):raise ValueError()
 def remaining():
  n=deadline-time.monotonic()
  if n<=0:raise ValueError()
  return n
 answers=socket.getaddrinfo(HOST,443,type=socket.SOCK_STREAM,proto=socket.IPPROTO_TCP);remaining()
 if not 1<=len(answers)<=16:raise ValueError()
 for family,kind,proto,_,target in answers:
  ip=ipaddress.ip_address(target[0])
  if not ip.is_global or ip.is_multicast or ip.is_unspecified or ip.is_loopback or ip.is_link_local or ip.is_reserved or family not in (socket.AF_INET,socket.AF_INET6)or kind!=socket.SOCK_STREAM or proto!=socket.IPPROTO_TCP or target[1]!=443:raise ValueError()
  if family==socket.AF_INET6 and (len(target)!=4 or target[2]!=0 or target[3]!=0):raise ValueError()
 family,kind,proto,_,target=answers[0];raw=None;tls=None;response=None
 try:
  raw=socket.socket(family,kind,proto);raw.settimeout(remaining());raw.connect(target)
  if raw.getpeername()[0]!=target[0]:raise ValueError()
  context=ssl.create_default_context()
  if context.check_hostname is not True or context.verify_mode!=ssl.CERT_REQUIRED:raise ValueError()
  raw.settimeout(remaining());tls=context.wrap_socket(raw,server_hostname=HOST);tls.settimeout(remaining())
  if tls.getpeername()[0]!=target[0]:raise ValueError()
  header=(method+' '+path+' HTTP/1.1\r\nHost: '+HOST+'\r\nContent-Type: application/json\r\nx-app-token: '+secret+'\r\nContent-Length: '+str(len(body))+'\r\nConnection: close\r\n\r\n').encode('ascii')
  tls.sendall(header+body);remaining();response=http.client.HTTPResponse(tls);response.begin();remaining()
  if response.headers.defects or type(response.status)is not int or not 200<=response.status<=599 or 300<=response.status<=399:raise ValueError()
  pairs=response.getheaders()
  if len(pairs)>32:raise ValueError()
  headers={}
  for k,v in pairs:
   key=k.lower()
   if key in headers or len(key)>100 or len(v)>2000 or '\r'in v or '\n'in v:raise ValueError()
   headers[key]=v
  if headers.get('content-encoding','identity').lower()!='identity'or headers.get('content-type','').split(';')[0].strip().lower()!='application/json':raise ValueError()
  length=headers.get('content-length');transfer=headers.get('transfer-encoding')
  if transfer is not None and (transfer.lower()!='chunked'or length is not None or not response.chunked):raise ValueError()
  if length is not None and (not length.isascii()or not length.isdecimal()or len(length)>8 or int(length)>MAX_RESPONSE_BYTES):raise ValueError()
  if transfer is None and length is None:raise ValueError()
  chunks=[];count=0
  while count<MAX_RESPONSE_BYTES:
   tls.settimeout(remaining());chunk=response.read(min(65536,MAX_RESPONSE_BYTES-count));remaining()
   if not chunk:break
   count+=len(chunk);chunks.append(chunk)
  if length is not None:
   if count!=int(length):raise ValueError()
  elif count==MAX_RESPONSE_BYTES:raise ValueError()
  wire=b''.join(chunks)
  # Accept bounded valid JSON only; detect escapes of secret as well as raw echo.
  value=json.loads(wire)
  if secret in wire.decode('utf-8')or secret in json.dumps(value,ensure_ascii=False):raise ValueError()
  return {'status':response.status,'body_b64':base64.b64encode(wire).decode('ascii')}
 finally:
  if response is not None:response.close()
  if tls is not None:tls.close()
  if raw is not None:raw.close()

def main():
 try:
  if os.environ:raise ValueError()
  raw=sys.stdin.buffer.read(32769)
  if len(raw)>32768:raise ValueError()
  v=json.loads(raw)
  if type(v)is not dict or set(v)!={'path','method','body_b64','secret'}:raise ValueError()
  body=base64.b64decode(v['body_b64'],validate=True)
  out=perform(v['path'],v['method'],body,v['secret'],deadline=time.monotonic()+20)
  sys.stdout.write(json.dumps(out,separators=(',',':')))
  return 0
 except Exception:return 70
if __name__=='__main__':raise SystemExit(main())
