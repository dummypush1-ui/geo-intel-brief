"""Opt-in local F13 peak-RSS diagnostic, never a host-capacity/ON approval.
Usage: python -B tests/measure_finder_changes_f13.py ARCHIVE SHA ROOT CASE
CASE: none, same, distinct-object. Each invocation must use a fresh process.
Same/distinct-object use one real artifact, NOT two chronological editions.
No source acquisition, provider request, environment mutation or activation.
"""
import sys,json,resource,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
def main(args):
 if len(args)!=4 or args[3]not in ('none','same','distinct-object'):raise SystemExit('Expected ARCHIVE SHA ROOT and none|same|distinct-object')
 from dataclasses import replace
 from integration import finder_binding_f8 as f8,finder_composition_f9 as f9,finder_changes_f13 as m
 archive,sha,root,case=args
 binding=f8.prepare({f8.FLAG:'true'},archive=archive,expected_sha256=sha,root=root)
 selection=f9.prepare({f9.FLAG:'true','PREVIEW_PUBLIC_SAMPLE_ENABLED':'true'},binding)
 baseline=None if case=='none'else binding if case=='same'else replace(binding)
 start=time.monotonic();service=m.Comparison(selection,baseline);result=service.read('HS','090121')
 # Linux ru_maxrss is KiB; other platforms may report bytes. Keep it explicit.
 print(json.dumps({'case':case,'peak_rss_raw':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'rss_unit':'KiB'if sys.platform.startswith('linux')else'platform_specific','elapsed_seconds':round(time.monotonic()-start,3),'state':result['state'],'projection_shared':service.before is service.after if service.before is not None else False,'package_sha256':binding.package_sha256,'scope':'local_process_peak_not_deployed_capacity_or_ON_proof','distinct_real_editions_tested':False}))
if __name__=='__main__':main(sys.argv[1:])
