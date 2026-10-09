# Backup request is not capability

ENABLE_TELEGRAM_BACKUP defaults false. An explicitly configured true value only
records requested configuration; it does not wire a sender or prove backup.
TELEGRAM_BACKUP_CAPABILITY remains held_pending_durable_adapter regardless.
RSS/GNews have no pre-write Telegram send. Durable full-record/outbox/journal,
exact destination acknowledgements and recovery checks remain required before
activation or a backup-completion claim. No existing flags, records or destinations
were changed in a live account. No mail or Telegram messages were sent.

Metadata cleanup stays held at the database/HTTP boundaries. A flag, message
link, stored short preview or hypothetical channel retention is not complete
recovery evidence and cannot authorize deletion or TTL. Existing records remain.

Apps Script's prior backup promise was already removed in unit180. Its current
collection wrapper does not promise backup. The edge guard's ban_seconds comment
now describes explicit/honeypot bans. Flood overflow refuses requests for the
rate window; it does not add a ban. Runtime rate/ban policy is unchanged.
