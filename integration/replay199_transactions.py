"""Closed explicit transaction provider holder. Native adapter UNAVAILABLE.
Only an injected synthetic test driver is supported in this source unit. This
holder does not establish any driver's correctness or authorize a live client.
"""
from integration.replay199_schema import ReplayRefused
class NoRetryTransactionProvider:
 __slots__=('client','_start','synthetic_only')
 def __init__(self,client,*,synthetic_session_factory=None):
  # Refuse real PyMongo clients. Test driver lives under tests, never selected
  # by runtime; no implicit start_session or native fallback can sneak in.
  if type(client).__module__.startswith('pymongo')or not callable(synthetic_session_factory):raise ReplayRefused('Native no-retry provider unavailable')
  self.client=client;self._start=synthetic_session_factory;self.synthetic_only=True
 def begin(self):return self._start()
