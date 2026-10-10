"""local CPython3.10.12 Linuxx86_64 venv build/import proof, negative input gates."""
import hashlib,json,pathlib,shutil,tempfile,unittest
from verify27 import verify,source
class Gates(unittest.TestCase):
 def test_artifact_negative_gates(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'x.whl').write_bytes(b'pinned');rows=[{'filename':'x.whl','sha256':hashlib.sha256(b'pinned').hexdigest()}];verify(p,rows)
   (p/'x.whl').write_bytes(b'tampered')
   with self.assertRaises(ValueError):verify(p,rows)
   (p/'x.whl').write_bytes(b'pinned')
   with self.assertRaises(ValueError):verify(p,[{'filename':'x.whl','sha256':'0'*64}])
   (p/'x.whl').unlink()
   with self.assertRaises(ValueError):verify(p,rows)
   (p/'x.whl').write_bytes(b'pinned');(p/'unpinned.whl').write_bytes(b'extra')
   with self.assertRaises(ValueError):verify(p,rows)
 def test_source_drift(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d);(p/'source.py').write_bytes(b'original');m={'anchor':'fixed','files':{'source.py':hashlib.sha256(b'original').hexdigest()}};source(p,m);(p/'source.py').write_bytes(b'drift')
   with self.assertRaises(ValueError):source(p,m)
if __name__=='__main__':unittest.main()
