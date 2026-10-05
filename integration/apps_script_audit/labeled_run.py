"""Trusted-source audit report wrapper, no isolation or no-I/O guarantee."""
import subprocess,sys
LABEL='[offline_not_production_not_receipt_proof] '
def main():
 try:
  result=subprocess.run(['node','integration/apps_script_audit/audit.js'],capture_output=True,text=True,timeout=10)
  for stream in (result.stdout,result.stderr):
   for line in stream.splitlines():print(LABEL+line)
  return result.returncode
 except Exception:
  print(LABEL+'audit child failed or timed out; no details logged')
  return 1
if __name__=='__main__':sys.exit(main())
