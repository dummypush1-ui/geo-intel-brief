"""Optional existing-schema review data only. No inspection or execution."""
from copy import deepcopy
from integration.native200_admission_preflight import VALIDATORS
from integration.native200_store import NAMES

_EXPECTED = (
    'collector_checkpoints197', 'collector_jobs197', 'collector_replay199',
    'finder_budget198', 'finder_replay199', 'native_guards200',
    'native_operations200', 'native_outcomes200',
)
# Independent snapshot of current constant data, not DB state or owner permission.
_SCHEMA = deepcopy(VALIDATORS)
_NAMES = tuple(sorted(NAMES))


def optional_schema_review(*, validation_level):
    """Reviewer explicitly chooses strict/moderate; this authorizes nothing."""
    if type(validation_level) is not str or validation_level not in ('strict', 'moderate'):
        raise ValueError('Explicit validation level required')
    if _NAMES != _EXPECTED or tuple(sorted(_SCHEMA)) != _EXPECTED:
        raise ValueError('Exact eight optional review names required')
    return {
        'state': 'optional_review_data_only',
        'ready': False,
        'executable': False,
        'live': False,
        'collection_existence_verified': False,
        'database': 'geo_intel',
        'request_data_not_executable': [
            {
                'collection_name': name,
                'proposed_validator': deepcopy(_SCHEMA[name]),
                'validation_level_choice': validation_level,
                'proposed_validation_action': 'error',
                'proposed_write_concern_data': {'w': 'majority', 'j': True, 'wtimeout': 5000},
            }
            for name in _NAMES
        ],
    }
