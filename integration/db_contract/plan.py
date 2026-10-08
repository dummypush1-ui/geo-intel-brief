# Copyright (c) 2026 Push. All rights reserved.
"""Least-privilege proposed resources. Assertions are not live grants or proof.

Never creates clients/roles/indexes/TTL, changes data, or consumes a candidate
handoff as a durable receipt. Collector collection names remain explicit inputs.
"""
import re
from copy import deepcopy

NAMES = {'full_records', 'collection_outbox', 'collection_control', 'backup_journal'}
FIXED = {'articles', 'events', 'mail_control', 'mail_receipts'}


def plan(collections):
    if type(collections) is not dict or set(collections) != NAMES:
        raise ValueError('Explicit collector mapping required')
    for value in collections.values():
        if type(value) is not str or not re.fullmatch(r'[a-z][a-z0-9_]{2,63}', value) or value.startswith('system') or value in FIXED:
            raise ValueError('Distinct reviewed non-system collection names required')
    if len(set(collections.values())) != len(collections):
        raise ValueError('Separate collector resources required')
    def privileges(mapping):
        return [{'resource': {'db': 'geo_intel', 'collection': name}, 'actions': actions[:]} for name, actions in mapping]
    full, outbox, control, journal = [collections[k] for k in ('full_records', 'collection_outbox', 'collection_control', 'backup_journal')]
    roles = {
        'public_reader': privileges([('articles', ['find'])]),
        'mail_worker': privileges([('articles', ['find', 'update']), ('events', ['find']), ('mail_control', ['find', 'update']), ('mail_receipts', ['find', 'insert', 'update'])]),
        'collection_writer': privileges([('articles', ['find', 'insert', 'update']), (full, ['find', 'insert']), (outbox, ['find', 'insert', 'update']), (control, ['find', 'update'])]),
        'backup_journal_worker': privileges([(full, ['find']), (journal, ['find', 'insert', 'update']), (outbox, ['find', 'update'])]),
    }
    # Mongo roles constrain collection/action, not which fields may be updated.
    # Mail's article update role is broader than emailed flags; app validation
    # and isolated credentials still matter. No false field-level least privilege.
    indexes = [
        {'collection': 'articles', 'name': 'article_url_unique_candidate', 'keys': [('url', 1)], 'options': {'unique': True}},
        {'collection': 'articles', 'name': 'mail_unsent_order_candidate', 'keys': [('emailed', 1), ('score', -1), ('published', -1), ('_id', -1)], 'options': {}},
        {'collection': 'articles', 'name': 'article_created_candidate', 'keys': [('created_at', -1)], 'options': {}},
        {'collection': 'events', 'name': 'event_date_candidate', 'keys': [('event_date', 1)], 'options': {}},
        {'collection': 'mail_receipts', 'name': 'mail_history_candidate', 'keys': [('channel_id', 1), ('created_at', -1)], 'options': {}},
    ]
    resources = sorted(FIXED | set(collections.values()))
    return {'scope': 'proposal_not_provisioned_or_authorized', 'database': 'geo_intel',
            'mapping': deepcopy(collections), 'roles': roles, 'inherited_roles': [],
            'indexes': indexes, 'ttl_indexes': [], 'automatic_deletion': False,
            'runtime_admin_actions': [], 'live_mapping_verified': False,
            'live_indexes_verified': False, 'provision_allowed': False,
            'no_ttl_resources': resources, 'retention': 'hold_until_separate_export_and_recovery_review',
            'collector_commit': 'transactional_preview_full_record_outbox_and_version_lease_fence_required',
            'backup_completion': 'all_required_pieces_authenticated_destination_hash_attempt_provider_ack',
            'unknown_send': 'latch_no_auto_retry', 'mail_receipt_scope': 'bridge_send_returned_not_delivery',
            'provisioning_review': ['role_availability_on_actual_Atlas_tier', 'exact_names_and_schema',
                                    'existing_duplicates_indexes_and_collations', 'query_explain_and_storage_cost',
                                    'transaction_capability_and_write_concern', 'separate_credential_authority']}


def retention_decision(record):
    fields = {'state', 'full_record_present', 'all_pieces_authenticated', 'unknown_send', 'export_verified'}
    if type(record) is not dict or set(record) != fields or type(record['state']) is not str or record['state'] not in ('pending', 'started', 'unknown', 'terminal'):
        raise ValueError('Closed retention evidence shape required')
    if any(type(record[k]) is not bool for k in fields - {'state'}):
        raise ValueError('Boolean evidence required')
    # Even a successful supplied tuple is not deletion authority or proof.
    eligible = (record['state'] == 'terminal' and record['full_record_present']
                and record['all_pieces_authenticated'] and not record['unknown_send'] and record['export_verified'])
    return {'scope': 'supplied_claims_not_recovery_proof', 'decision': 'eligible_for_owner_retention_review' if eligible else 'hold',
            'delete_allowed': False, 'ttl_allowed': False, 'current_evidence_required': True}
