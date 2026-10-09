"""Native read-only coverage adapter. No public put or unguarded write."""
from integration.native200_admission_store import AdmissionStore
from integration.collector197_coverage import CoverageCheckpoints,CoverageRefused,coverage,coverage_hash
from collector110_prep.input_budget import capture
from collector109_prep.checkpoint import run_inputs,digest
from collector110_prep.durable_checkpoint import _encode
class NativeCoverageCheckpoints:
 def __init__(self,collection):
  if type(collection)is not AdmissionStore or collection.name!='collector_checkpoints197':raise CoverageRefused('Exact admission checkpoint store')
  self.c=collection
 _identity=staticmethod(CoverageCheckpoints._identity)
 get=CoverageCheckpoints.get

def checkpoint_row(key,fence,inputs,source_coverage):
 """Pure exact schema/hash preparation, never writes."""
 try:
  CoverageCheckpoints._identity(key,fence)
  bound=capture({'inputs':inputs,'coverage':source_coverage})['captured'];v=bound['inputs']
  if type(v)is not dict or set(v)!={'candidates','active_categories','threshold'}:raise ValueError()
  v=run_inputs(v['candidates'],v['active_categories'],v['threshold']);c=coverage(bound['coverage'])
  return {'_id':key,'fence':str(fence),'version':2,'input_hash':digest(key,fence,v),'coverage_hash':coverage_hash(key,fence,c),'inputs':_encode(v),'coverage':_encode(c)}
 except Exception:raise CoverageRefused('Exact bounded checkpoint preparation')from None
