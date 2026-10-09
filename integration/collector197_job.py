"""Default-OFF one-shot job composition. No HTTP, schedule or automatic recovery.
Injected evidence is mandatory and does not itself grant owner write authority.
No builtin production provider; owner-operated containment/binding is separate.
"""
import time,json,sys,resource
from integration.collector197_job_runtime import (JobRefused,require_job_provider,
    read_job_facts,PARENT_BYTES)
from integration.collector197_config import configure,GATES
from integration.collector197_http import create_writer_client,_Client
from integration.collector197_preflight import inspect_writer
from integration.collector197_coverage import CoverageCheckpoints
from integration.collector197_orchestrator import run_cycle
from integration.collector197_coordinator import supervised_candidates
from integration.geo_article_writer import GeoArticleWriter

def run_job(values,*,nonce,runtime_evidence=None,client_factory=None,clock=None,fetch=None):
    clock=clock or(lambda:int(time.time()))
    if type(values)is not dict or any(type(k)is not str or type(v)is not str for k,v in values.items()):raise JobRefused('Exact job configuration required')
    off={**values,'COLLECTION_ENABLED':'false'};configure(off,{})
    switch=values.get('COLLECTION_ENABLED','false')
    if switch not in ('false','true'):raise JobRefused('Exact job switch required')
    if switch=='false':return {'state':'disabled','activation_authority':False}
    # Must already be launched with bounds; do not pretend an observation sets them.
    require_job_provider(runtime_evidence,clock)
    facts=read_job_facts()
    if facts['supported']is not True:raise JobRefused('Observed job containment unavailable')
    from collector130_prep.base_profile import compile_profile
    keys={'MAX_ITEMS_PER_FEED','REQUEST_TIMEOUT','LOOKBACK_HOURS','ACTIVE_CATEGORIES','DEDUPE_THRESHOLD','ENABLE_FULL_TEXT','ENABLE_GNEWS','ENABLE_TELEGRAM_BACKUP'}
    profile=compile_profile({k:v for k,v in values.items()if k in keys})
    fp=values.get('COLLECTOR_PROFILE_FINGERPRINT','')
    if type(fp)is not str or len(fp)!=64 or any(c not in '0123456789abcdef'for c in fp):raise JobRefused('Exact profile fingerprint required')
    if type(nonce)is not str or not 20<=len(nonce)<=80 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-'for c in nonce):raise JobRefused('Exact job nonce required')
    config=configure(values,dict.fromkeys(GATES,True))
    client=None
    try:
        client=(client_factory or create_writer_client)(values['GEO_WRITER_MONGODB_URI'])
        handles=inspect_writer(client,fp)
        # Refresh before claim; no evidence from an earlier run can drive this one.
        require_job_provider(runtime_evidence,clock)
        if read_job_facts()['supported']is not True:raise JobRefused('Job guard changed')
        writer=GeoArticleWriter(_Client(handles['articles']),review={'mapping':('geo_intel','articles'),'write_permission':True,'unique_url_index_verified':True,'source_contract_verified':True})
        def bounded_fetch(**kw):
            require_job_provider(runtime_evidence,clock)
            return supervised_candidates(**kw,max_items=profile['max_items'],lookback_hours=profile['lookback_hours'],request_timeout=profile['timeout'],job_mode=True)
        return run_cycle(config,ledger=handles['ledger'],checkpoints=CoverageCheckpoints(handles['checkpoints']),nonce=nonce,fetch=fetch or bounded_fetch,categories=profile['active_categories'],threshold=profile['threshold'],clock=clock,writer=writer)
    except Exception:raise JobRefused('Job held; inspect durable state, never retry blindly')from None
    finally:
        if client is not None:
            try:client.close()
            except Exception:pass

def main(argv=None,*,values=None,runtime_evidence=None,output=None):
    """Owner-controlled launcher injects scoped provider; no env-ready shortcut.
    Direct CLI is read-only diagnostics. No URI, nonce or activation from argv.
    """
    argv=sys.argv[1:]if argv is None else argv
    output=output or sys.stdout
    if argv!=['--diagnose']:
        output.write(json.dumps({'error':'explicit_read_only_diagnostic_required'})+'\n');return 2
    output.write(json.dumps(read_job_facts(),sort_keys=True)+'\n');return 0

if __name__=='__main__':raise SystemExit(main())
