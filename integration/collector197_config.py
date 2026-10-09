"""Source-only collector configuration contract, not production activation.
No environment reads, URI parsing/client creation, role probes or network.
Injected preflight assertions are NOT live verification or owner permission.
197b must supply independently verified proofs and supervised adapters.
"""
from dataclasses import dataclass

class ConfigRefused(ValueError):
    pass

GATES = frozenset(('writer_role', 'unique_url_index', 'no_article_ttl',
                   'durable_mapping', 'majority_journal', 'runtime_bwrap',
                   'free_capacity', 'source_catalog', 'owner_activation'))

@dataclass(frozen=True)
class CollectorConfig:
    enabled: bool
    writer_env: str = 'GEO_WRITER_MONGODB_URI'
    article_mapping: tuple = ('geo_intel', 'articles')
    ledger_mapping: tuple = ('geo_intel', 'collector_jobs197')
    checkpoint_mapping: tuple = ('geo_intel', 'collector_checkpoints197')
    whole_cycle_seconds: int = 90
    per_feed_seconds: int = 25


def configure(values, proofs):
    """Validate explicit supplied configuration before any side effect.
    OFF needs no writer credentials/proofs. Unsupported features always refuse.
    No fallback to the public reader or legacy writer variable is permitted.
    """
    if type(values) is not dict or type(proofs) is not dict:
        raise ConfigRefused('Exact configuration required')
    switch = values.get('COLLECTION_ENABLED', 'false')
    if type(switch) is not str or switch not in ('false', 'true'):
        raise ConfigRefused('Exact collection switch required')
    for flag in ('ENABLE_FULL_TEXT', 'ENABLE_GNEWS', 'ENABLE_TELEGRAM_BACKUP'):
        if values.get(flag, 'false') != 'false' or type(values.get(flag, 'false')) is not str:
            raise ConfigRefused('Unsupported collector feature')
    if switch == 'false':
        return CollectorConfig(False)
    if set(proofs) != GATES or any(proofs[k] is not True for k in GATES):
        raise ConfigRefused('Complete independently verified preflight required')
    uri = values.get('GEO_WRITER_MONGODB_URI')
    if type(uri) is not str or not uri.strip() or len(uri) > 4096:
        raise ConfigRefused('Dedicated writer configuration required')
    # Values are never retained or echoed. Equal strings do not prove roles;
    # refuse obvious aliasing in addition to requiring a separate role proof.
    if uri in (values.get('GEO_MONGODB_URI'), values.get('MONGODB_URI')):
        raise ConfigRefused('Dedicated writer must not alias another client')
    return CollectorConfig(True)
