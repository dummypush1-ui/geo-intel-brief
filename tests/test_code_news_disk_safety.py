import unittest,tempfile,json,hashlib,struct,os,threading,importlib.util
from pathlib import Path
from unittest.mock import patch
from integration.code_news_disk import DiskLinks,RECORD
from integration.code_news_links import Refused
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def folder(self,bad=False):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);p=Path(temp.name);groups=[[dict(system='HS',edition='2022',code=code,description=description,state='resolved')]for code,description in [('1006','Rice'),('8517','Phones')]];raw=b'';index=b''
  for group in groups:
   data=json.dumps(group).encode();index+=RECORD.pack(group[0]['code'].encode().ljust(12,b' '),len(raw),len(data));raw+=data
  if bad:index=index[:12]+struct.pack('>Q',1)+index[20:]
  (p/'codes.idx').write_bytes(index);(p/'rows.jsonl').write_bytes(raw);(p/'manifest.json').write_text(json.dumps({'format':'code_news_flat_v1','code_count':2,'files':{n:{'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}for n,data in [('codes.idx',index),('rows.jsonl',raw)]}}));return p
 def model(self):
  m=DiskLinks(self.folder());self.addCleanup(m.close);return m
 def test_multithread_forced_interleave_News_then_leaf(self):
  m=self.model();start=threading.Barrier(4);inside=threading.Event();release=threading.Event();news=threading.Lock();results=[];errors=[];original=os.pread;count=[0]
  def read(fd,length,offset):
   count[0]+=1
   if count[0]==1:inside.set();self.assertTrue(release.wait(2))
   return original(fd,length,offset)
  def worker(code,use_news):
   try:
    start.wait(2)
    if use_news:
     with news:results.append(m.resolve(code))
    else:results.append(m.resolve(code))
   except Exception as e:errors.append(e)
  with patch('integration.code_news_disk.os.pread',side_effect=read):
   threads=[threading.Thread(target=worker,args=(code,i==0))for i,code in enumerate(['1006','8517','1006'])]
   for t in threads:t.start()
   start.wait(2);self.assertTrue(inside.wait(2));release.set()
   for t in threads:t.join(3);self.assertFalse(t.is_alive())
  self.assertEqual(errors,[]);self.assertEqual(sorted(r['items'][0]['description']for r in results),['Phones','Rice','Rice'])
 def test_old_seek_read_forced_race_reproduced(self):
  # The old algorithm shares seek/read position. Force both seeks before reads.
  m=self.model();fd=os.open(m.folder/'rows.jsonl',os.O_RDONLY);self.addCleanup(lambda:os.close(fd));barrier=threading.Barrier(2);results=[]
  def old_read(code,offset,length):
   os.lseek(fd,offset,os.SEEK_SET);barrier.wait(2);raw=os.read(fd,length)
   try:row=json.loads(raw);results.append(row[0]['code']==code)
   except Exception:results.append(False)
  keys=[RECORD.unpack_from(m.index,i*RECORD.size)for i in range(2)];threads=[threading.Thread(target=old_read,args=(key.rstrip(b' ').decode(),offset,length))for key,offset,length in keys]
  for t in threads:t.start()
  for t in threads:t.join(3)
  self.assertFalse(all(results));self.assertEqual(len(results),2)
 def test_parse_filter_callback_leaf_released(self):
  m=self.model();original=json.loads;seen=[]
  def parse(*args,**kwargs):seen.append(m.read_lock.locked());return original(*args,**kwargs)
  with patch('integration.code_news_disk.json.loads',side_effect=parse):self.assertEqual(m.resolve('8517')['items'][0]['description'],'Phones')
  self.assertEqual(seen,[False])
 def test_OSError_short_closed_idempotent(self):
  m=self.model()
  for effect in [OSError('private'),None]:
   with patch('integration.code_news_disk.os.pread',side_effect=effect,return_value=b''):
    with self.assertRaises(Refused):m.resolve('8517')
  fd=m.rows_fd;m.close();m.close()
  with patch('integration.code_news_disk.os.pread',side_effect=AssertionError('reusedfd')):
   with self.assertRaises(Refused):m.resolve('8517')
   with self.assertRaises(Refused):m.resolve('bad')
  self.assertIsNone(m.rows_fd)
 def test_close_waits_read_no_reusedfd(self):
  m=self.model();inside=threading.Event();release=threading.Event();closed=threading.Event();result=[];original=os.pread
  def read(*args):inside.set();self.assertTrue(release.wait(2));return original(*args)
  with patch('integration.code_news_disk.os.pread',side_effect=read):
   t=threading.Thread(target=lambda:result.append(m.resolve('8517')));t.start();self.assertTrue(inside.wait(2));close=threading.Thread(target=lambda:(m.close(),closed.set()));close.start();self.assertFalse(closed.wait(.03));release.set();t.join(3);close.join(3)
  self.assertTrue(closed.is_set());self.assertEqual(result[0]['items'][0]['description'],'Phones')
  with self.assertRaises(Refused):m.resolve('8517')
 def test_constructor_failure_fd_count(self):
  p=self.folder(bad=True);before=len(list(Path('/proc/self/fd').iterdir()))
  for _ in range(5):
   with self.assertRaises(Refused):DiskLinks(p)
  self.assertEqual(len(list(Path('/proc/self/fd').iterdir())),before)
  p=self.folder()
  with patch('integration.code_news_disk.os.open',side_effect=OSError('no')):
   with self.assertRaises(OSError):DiskLinks(p)
  self.assertEqual(len(list(Path('/proc/self/fd').iterdir())),before)
 def test_positional_unbuffered_read_bound(self):
  m=self.model()
  with patch('integration.code_news_disk.os.pread',wraps=os.pread)as read:
   m.resolve('1006');m.resolve('8517')
  self.assertEqual(read.call_count,2);self.assertTrue(all(c.args[0]==m.rows_fd and c.args[1]<=65536 for c in read.call_args_list));self.assertFalse(hasattr(m,'rows_file'))

 def test_actual_old_class_barrier_race_and_equal_outputs(self):
  # Kept fixture source passed from exact baseline; not production dependency.
  baseline=ROOT/'tests'/'fixtures'/'code_news_disk_before_safety.txt'
  namespace={};exec(compile(baseline.read_text(),str(baseline),'exec'),namespace);Old=namespace['DiskLinks'];folder=self.folder();old=Old(folder);new=DiskLinks(folder);self.addCleanup(old.close);self.addCleanup(new.close)
  for code in ['1006','8517','10','9999','invalid']:
   self.assertEqual(json.dumps(old.resolve(code),sort_keys=True),json.dumps(new.resolve(code),sort_keys=True))
  class RacedFile:
   def __init__(self,file):self.file=file;self.barrier=threading.Barrier(2)
   def seek(self,offset):self.file.seek(offset);self.barrier.wait(2)
   def read(self,length):return self.file.read(length)
   def close(self):self.file.close()
  old.rows_file=RacedFile(old.rows_file);results=[];errors=[]
  def run(code):
   try:results.append(old.resolve(code))
   except Exception as e:errors.append(e)
  threads=[threading.Thread(target=run,args=(code,))for code in ['1006','8517']]
  for t in threads:t.start()
  for t in threads:t.join(3);self.assertFalse(t.is_alive())
  self.assertTrue(errors or len({r['items'][0]['code']for r in results})!=2)
 def test_real_baseline_byte_equal_ambiguous_conflict_omission(self):
  baseline=ROOT/'tests'/'fixtures'/'code_news_disk_before_safety.txt';namespace={};exec(compile(baseline.read_text(),str(baseline),'exec'),namespace);old=namespace['DiskLinks'](ROOT/'integration/code_news_index');new=DiskLinks(ROOT/'integration/code_news_index');self.addCleanup(old.close);self.addCleanup(new.close)
  for args in [('100630','HS','2022'),('1006',),('010129','ZA'),('030290','CN'),('10','HS'),('999999999999',),('8517','HS','2022')]:self.assertEqual(json.dumps(old.resolve(*args),ensure_ascii=False),json.dumps(new.resolve(*args),ensure_ascii=False))
