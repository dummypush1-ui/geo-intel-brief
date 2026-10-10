"""local workflow preflight/package inventory; Docker NOT RUN; item 29 OPEN"""
import unittest,pathlib,tempfile,shutil,json,hashlib,sys
import preflight as p
ROOT=pathlib.Path(sys.argv[1]).resolve();sys.argv=sys.argv[:1]
class Negatives(unittest.TestCase):
 def setup_case(self):
  d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);r=pathlib.Path(d.name);shutil.copytree(ROOT/'runtime_build',r/'runtime_build');(r/'.github/workflows').mkdir(parents=True);shutil.copyfile(ROOT/'.github/workflows/runtime-build-review.yml',r/'.github/workflows/runtime-build-review.yml');return r
 def refused(self,mutator):
  r=self.setup_case();mutator(r)
  with self.assertRaises(p.Refused):p.inspect(r)
 def test_baseline_blocked_not_pass(self):
  r=p.inspect(ROOT);self.assertEqual(r['summary'],'preflight: 1 blocked input, build not attempted');self.assertEqual(r['rows'][1]['status'],'BLOCKED');self.assertEqual(r['rows'][1]['reason'],'inputs/application.lock absent');self.assertEqual(r['totals']['PASS'],1);self.assertEqual(r['totals']['BLOCKED'],3)
 def test_old_sgml_hash_rejected(self):
  self.refused(lambda r:(r/'runtime_build/inputs/application.lock').write_text('sgmllib3k==1.0.0 --hash=sha256:d697b1ce32621812e6fbf5d3dac57818192068f47e4b6f39bc76e14a8fb4c534'))
 def test_placeholder_rejected(self):self.refused(lambda r:(r/'runtime_build/inputs/application.lock').write_text('PENDING'))
 def test_workflow_if(self):
  def edit(r):
   f=r/'.github/workflows/runtime-build-review.yml';f.write_text(f.read_text().replace("if: github.repository == 'dummypush1-ui/geo-intel-brief'",'if: true'))
  self.refused(edit)
 def test_permissions(self):
  def edit(r):
   f=r/'.github/workflows/runtime-build-review.yml';f.write_text(f.read_text().replace('contents: read','contents: write'))
  self.refused(edit)
 def test_docker_gate_removed(self):
  def edit(r):
   f=r/'runtime_build/Dockerfile.candidate';f.write_text(f.read_text().replace('RUN test -f /reviewed-inputs/application.lock',''))
  self.refused(edit)
 def test_missing(self):self.refused(lambda r:(r/'runtime_build/inputs/apt.sources').unlink())
 def test_extra(self):self.refused(lambda r:(r/'runtime_build/extra').write_text('extra'))
 def test_symlink(self):self.refused(lambda r:(r/'runtime_build/link').symlink_to('Dockerfile.candidate'))
 def test_tampered_anchor(self):self.refused(lambda r:(r/'runtime_build/inputs.sha256').write_text('0'*64))
 def test_manifest_cycle(self):
  def edit(r):
   f=r/'runtime_build/inputs-manifest.json';m=json.loads(f.read_text());m['files']['inputs-manifest.json']='0'*64;raw=json.dumps(m).encode();f.write_bytes(raw);(r/'runtime_build/inputs.sha256').write_text(hashlib.sha256(raw).hexdigest())
  self.refused(edit)
 def test_args_drift(self):
  def edit(r):
   f=r/'runtime_build/build-args.json';m=json.loads(f.read_text());m['GCC_VERSION']='latest';f.write_text(json.dumps(m))
  self.refused(edit)
if __name__=='__main__':unittest.main()
