"""Caller-supplied candidates to the in-memory fake store only.

Not imported by runtime. No fetching, scheduling, real persistence or delivery.
This connects the reviewed processing and fake-writer seams without selecting
production collection names or inferring production configuration.
"""
from integration.collection_prepare import prepare_candidates
from integration.fake_collection_writer import FakeCollectionWriter, plain


def run_offline_cycle(project, candidates, active_categories, threshold, clock,
                      writer, failed_urls=()):
    if type(project) is not str or project not in ('geo', 'brics'):
        raise ValueError('Exact project string required')
    if type(active_categories) is not list or not active_categories or any(
            type(category) is not str or not category for category in active_categories):
        raise ValueError('Exact category list and strings required')
    # An arbitrary writer/callback could introduce an external effect. Accept
    # only the exact fixture type, not a duck-typed or subclassed backend.
    if type(writer) is not FakeCollectionWriter:
        raise ValueError('Exact in-memory fixture writer required')
    if any(type(store) is not dict or not plain(store)
           for store in (writer._geo, writer._brics)):
        raise ValueError('Plain in-memory fixture state required')
    if type(candidates) is not list or len(candidates) > 1000 or not plain(candidates):
        raise ValueError('Bounded plain JSON candidates required')
    prepared = prepare_candidates(project, candidates, active_categories, threshold)
    result = FakeCollectionWriter.write(writer, project, prepared['items'], clock, failed_urls)
    return {
        'project': project,
        'state': 'offline_fake_cycle_only',
        'candidate_count': prepared['candidate_count'],
        'deduped_count': prepared['deduped_count'],
        'prepared_count': prepared['prepared_count'],
        'writer': result,
        'network': False,
        'live_writes': False,
        'delivery': False,
    }
