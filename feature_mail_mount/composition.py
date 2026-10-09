"""Explicit default-OFF private mail composition. Never sends or creates clients."""
from .http import blueprint
from .store import MongoMailStore
class LegacyMailHeld(PermissionError):
 pass

def compose_private_mail(app,*,enabled=False,store=None,secret=None,clock=None):
 if type(enabled) is not bool:raise ValueError('Explicit mail gate required')
 if enabled is False:
  if any(v is not None for v in (store,secret,clock)):raise ValueError('Disabled mail accepts no capabilities')
  app.extensions['mail_receipt_mode']='off'
  return app
 if not isinstance(store,MongoMailStore):raise ValueError('Reviewed durable MongoMailStore required')
 if store.policy!='displayed':raise ValueError('Displayed-only source contract required; live marking approval separate')
 if app.extensions.get('mail_receipt_mode') is not None:raise ValueError('Mail composition already configured')
 app.register_blueprint(blueprint(store,secret=secret,clock=clock))
 app.extensions['mail_receipt_mode']='private_receipt_bridge_no_send'
 return app

def hold_legacy_mail(*args,**kwargs):
 raise LegacyMailHeld('Legacy send/mark held: use reviewed durable receipt bridge; no automatic resend')
