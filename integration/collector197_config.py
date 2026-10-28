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
    # Full text and Google News have reviewed bounded fetchers in collector197_job.
    # Telegram backup is owner-gated: it needs an explicit approval text plus a bot
    # token and chat id in the job payload, checked here and again in the entry.
    for flag in ('ENABLE_FULL_TEXT', 'ENABLE_GNEWS', 'ENABLE_TELEGRAM_BACKUP'):
        if type(values.get(flag, 'false')) is not str or values.get(flag, 'false') not in ('true', 'false'):
            raise ConfigRefused('Exact feature switch required')
    if values.get('ENABLE_TELEGRAM_BACKUP', 'false') == 'true':
        import re
        t, c, a = values.get('TELEGRAM_BACKUP_BOT_TOKEN'), values.get('TELEGRAM_BACKUP_CHAT_ID'), values.get('TELEGRAM_BACKUP_APPROVAL')
        if (type(t) is not str or not re.fullmatch(r'[0-9]{5,15}:[A-Za-z0-9_-]{20,80}', t) or type(c) is not str
                or not re.fullmatch(r'@[A-Za-z0-9_]{5,32}|-?[0-9]{1,20}', c) or type(a) is not str or not 8 <= len(a) <= 200):
            raise ConfigRefused('Telegram backup needs owner approval, token and chat id')
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
