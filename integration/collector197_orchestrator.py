"""Injected durable orchestration candidate. Production stays OFF.
No HTTP mount/client/env/transport/process creation, timer or recovery takeover.
The supplied fetch adapter MUST eventually be a hard supervised whole-cycle
runner (197b). Deadline checks here are guards, NOT callback preemption.
"""
import time
from datetime import datetime, timezone
from collector108_prep.durable_ledger import DurableLedger, LedgerRefused
from collector110_prep.durable_checkpoint import DurableCheckpoints
from collector110_prep.input_budget import capture
from collector109_prep.checkpoint import run_inputs
from collector111_prep.drive_durable import _receipt
from integration.geo_collector_contract import prepare_geo_documents
from integration.geo_article_writer import GeoArticleWriter
from integration.collector197_config import CollectorConfig
from integration.collector197_coverage import CoverageCheckpoints,coverage,catalog_fingerprint

class CycleRefused(ValueError):
    pass


def _concerns(collection):
    try:
        wc = collection.write_concern.document
        rc = collection.read_concern.document
        if (type(wc) is not dict or wc.get('w') != 'majority' or wc.get('j') is not True
                or type(wc.get('wtimeout')) is not int or not 1 <= wc['wtimeout'] <= 30000
                or type(rc) is not dict or rc.get('level') != 'majority'):
            raise ValueError()
    except Exception:
        raise CycleRefused('Reviewed durable concerns required') from None


def run_cycle(config, *, ledger, checkpoints, nonce, fetch, categories, threshold,
              clock, monotonic=time.monotonic, writer=None, hard_deadline=None):
    if type(config) is not CollectorConfig or config != CollectorConfig(config.enabled):
        raise CycleRefused('Fixed configuration contract required')
    if type(config.enabled) is not bool:
        raise CycleRefused('Exact switch required')
    if not config.enabled:
        return {'state': 'disabled', 'production_mounted': False}
    if (type(ledger) is not DurableLedger or type(checkpoints) not in (DurableCheckpoints,CoverageCheckpoints)
            or (writer is not None and type(writer) is not GeoArticleWriter)
            or not callable(fetch) or not callable(clock) or not callable(monotonic)):
        raise CycleRefused('Exact injected adapters required')
    _concerns(ledger.c)
    _concerns(checkpoints.c)
    # Validate processing configuration before ledger/fetch mutation.
    run_inputs([], categories, threshold)
    start = monotonic()
    if type(start) not in (int, float) or not 0 <= start < float('inf'):
        raise CycleRefused('Monotonic clock required')
    deadline = start + config.whole_cycle_seconds
    if hard_deadline is not None:
        if type(hard_deadline)not in (int,float) or not start<hard_deadline<=deadline:
            raise CycleRefused('Bounded installation deadline required')
        deadline=hard_deadline

    def now():
        n = clock()
        if type(n) is not int or n < 0:
            raise CycleRefused('Exact integer clock required')
        return n

    def budget():
        n = monotonic()
        if type(n) not in (int, float) or not start <= n < deadline:
            raise CycleRefused('Whole cycle deadline exceeded')

    job = ledger.submit(nonce, now())
    key, fence = job['key'], job['fence']
    # Replay returns status only. Never let a second invocation fetch or drive
    # an existing running/checkpoint/write-started job, even with the same nonce.
    if job['phase'] != 'accepted':
        out={'state': 'replay_held', 'job': key, 'phase': job['phase'], 'production_mounted': False}
        if type(checkpoints)is CoverageCheckpoints and job['phase'] in ('fetch_complete','prepare_complete','write_started','completed','uncertain_after_write'):
            out['coverage']=checkpoints.get(key,fence)['coverage']
        return out
    try:
        ledger.advance(key, fence, 'running', now(), {})
    except LedgerRefused:
        raise CycleRefused('Exclusive claim refused; no fetch') from None
    phase = 'running'
    try:
        budget()
        # CAS claim is held before callback entry. No URI/secret is supplied.
        raw = fetch(deadline=deadline, per_feed_seconds=config.per_feed_seconds)
        budget()
        ledger.heartbeat(key, fence, now())
        source_coverage=None
        if type(checkpoints)is CoverageCheckpoints:
            envelope=capture(raw)['captured']
            if type(envelope)is not dict or set(envelope)!={'candidates','source_states','all_sources_healthy'}:raise CycleRefused('Full fetch coverage required')
            source_coverage=coverage({'catalog':catalog_fingerprint(),'source_states':envelope['source_states'],'all_sources_healthy':envelope['all_sources_healthy']})
            raw=envelope['candidates']
        bound = capture({'candidates': raw, 'active_categories': categories,
                         'threshold': threshold})['captured']
        inputs = run_inputs(bound['candidates'], bound['active_categories'], bound['threshold'])
        if type(checkpoints)is CoverageCheckpoints:
            checkpoints.put(key,fence,inputs,source_coverage)
            full=checkpoints.get(key,fence);saved=full['inputs'];source_coverage=full['coverage']
        else:
            checkpoints.put(key, fence, inputs)
            saved = checkpoints.get(key, fence)
        ledger.advance(key, fence, 'fetch_complete', now(), {'fetched': len(saved['candidates'])})
        phase = 'fetch_complete'
        docs = prepare_geo_documents(saved['candidates'], saved['active_categories'], saved['threshold'])['documents']
        budget()
        counts = {'fetched': len(saved['candidates']), 'prepared': len(docs), 'attempted': len(docs)}
        ledger.advance(key, fence, 'prepare_complete', now(), counts)
        phase = 'prepare_complete'
        if writer is None:
            return {'state': 'held_before_write', 'job': key, 'phase': phase, 'production_mounted': False, **({'coverage':source_coverage}if source_coverage is not None else{})}
        budget()
        # The only winning CAS caller may enter article write. From this point
        # all failures, including receipts/clock/deadline/store loss, latch.
        ledger.advance(key, fence, 'write_started', now(), counts)
        phase = 'write_started'
        ledger.heartbeat(key, fence, now())
        checked = _receipt(writer.write(docs, datetime.fromtimestamp(now(), timezone.utc)), len(docs))
        budget()
        if checked is None or checked['failed']:
            raise CycleRefused('Write reconciliation required')
        counts.update(checked)
        ledger.advance(key, fence, 'completed', now(), counts)
        return {'state': 'completed', 'job': key, 'counts': counts, 'production_mounted': False, **({'coverage':source_coverage}if source_coverage is not None else{})}
    except Exception:
        # Unknown CAS failure could have landed. Read source state; do NOT
        # downgrade a write ticket or clear uncertain/expired jobs.
        try:
            current = ledger.status(key)['phase']
            if current == 'write_started':
                ledger.advance(key, fence, 'uncertain_after_write', now(), {})
            elif current in ('running', 'fetch_complete', 'prepare_complete'):
                ledger.advance(key, fence, 'failed_before_write', now(), {})
        except Exception:
            pass
        raise CycleRefused('Cycle held; inspect durable status before any further action') from None
