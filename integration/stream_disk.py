"""Explicit local stream config CAS. Not selected by any runtime.

Cooperative Linux flock, same-directory replace and fsync. Operator must verify
persistent volume/permissions/backups before activation. No live/default path,
network or availability polling. Not hostile shared-directory safe.
"""
import os,stat,fcntl,tempfile,hashlib
from pathlib import Path
from integration.stream_revision import revise
from integration.stream_config import configured_streams,MAX_BYTES
class StreamDiskError(ValueError):pass
class StreamDiskConflict(StreamDiskError):pass
class StreamDiskUncertain(StreamDiskError):pass
class DiskStreams:
 def __init__(self,path,*,verified_local=False):
  if verified_local is not True or type(path) is not str or not os.path.isabs(path) or '\x00' in path:raise StreamDiskError('Explicit reviewed absolute local path required')
  self._path=Path(path)
  # No arbitrary default mkdir/create. Operator prepares owned directory and
  # existing valid file; constructor refuses symlink parent chain.
  for p in (self._path.parent,*self._path.parent.parents):
   s=p.lstat()
   if stat.S_ISLNK(s.st_mode) or not stat.S_ISDIR(s.st_mode):raise StreamDiskError('Owned local directory required')
  if self._path.parent.stat().st_uid!=os.getuid() or self._path.parent.stat().st_mode&0o022:raise StreamDiskError('Private owned directory required')
 def _read(self):
  fd=None
  try:
   fd=os.open(self._path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
   s=os.fstat(fd)
   if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.getuid() or s.st_mode&0o077 or s.st_nlink!=1 or not 0<s.st_size<=MAX_BYTES:raise ValueError()
   chunks=[];size=0
   while True:
    b=os.read(fd,min(4096,MAX_BYTES+1-size))
    if not b:break
    size+=len(b)
    if size>MAX_BYTES:raise ValueError()
    chunks.append(b)
   return b''.join(chunks)
  finally:
   if fd is not None:os.close(fd)
 def _lock(self):
  fd=None
  try:
   fd=os.open(str(self._path)+'.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
   s=os.fstat(fd)
   if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.getuid() or s.st_mode&0o077 or s.st_nlink!=1:raise ValueError()
   fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
   return fd
  except BaseException:
   if fd is not None:os.close(fd)
   raise
 def read(self,observed_at):
  fd=None;failed=False
  try:
   fd=self._lock();raw=self._read();result=configured_streams(raw,observed_at)
   result['scope']='explicit_local_file_not_live_status';result['persistence']='local_filesystem_only'
  except BaseException:failed=True
  finally:
   if fd is not None:os.close(fd)
  if failed:raise StreamDiskError('Local stream snapshot unavailable')
  return result
 def update(self,expected_revision,operation,fields,observed_at):
  lock=None;temp=None;fd=None;committed=False;conflict=False;failed=False
  try:
   lock=self._lock();raw=self._read()
   if type(expected_revision) is not str or hashlib.sha256(raw).hexdigest()!=expected_revision:conflict=True;raise ValueError()
   result=revise(raw,expected_revision,operation,fields,observed_at)
   if result['changed']:
    fd,temp=tempfile.mkstemp(prefix='.'+self._path.name+'.',dir=self._path.parent)
    os.fchmod(fd,0o600)
    data=memoryview(result['bytes'])
    while data:
     written=os.write(fd,data)
     if written<=0:raise OSError()
     data=data[written:]
    os.fsync(fd);os.close(fd);fd=None
    os.replace(temp,self._path);committed=True;temp=None
    directory=os.open(self._path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(directory)
    finally:os.close(directory)
   result={k:v for k,v in result.items() if k!='bytes'}
   result['scope']='explicit_local_file_revision';result['persistence']='fsync_completed_local_only'
  except BaseException:failed=True
  finally:
   if fd is not None:os.close(fd)
   if temp is not None:
    try:os.unlink(temp)
    except OSError:pass
   if lock is not None:os.close(lock)
  if conflict:raise StreamDiskConflict('Stream revision conflict')
  if failed:
   if committed:raise StreamDiskUncertain('Stream replace completed, durability unverified')
   raise StreamDiskError('Local stream update unavailable')
  return result
