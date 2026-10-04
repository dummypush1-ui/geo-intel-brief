"""Explicit private fixture composition from supplied original YAML bytes.

No source paths, live clients, persistent writes or polling. Not production
configuration discovery. The dashboard shows captured source configuration;
management edits affect a separate RAM copy only, never that captured snapshot.
"""
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from integration.stream_config import configured_streams
from integration.brics_streams import FixtureStreams
from integration.dashboard_snapshots import DashboardSnapshots
from integration.news_api import create_app

def create_stream_fixture(raw,observed_at,*,authorize,allowed_origin):
 if not callable(authorize):raise ValueError('Explicit private authorization required')
 snapshot=configured_streams(raw,observed_at)
 # Capture dates may be old; never claim freshness. Reject impossible future capture.
 if observed_at.astimezone(timezone.utc)>datetime.now(timezone.utc)+timedelta(minutes=5):raise ValueError('Future capture time')
 def strict_authorize(request):
  if request.host_url.rstrip('/')!=allowed_origin:return False
  try:return authorize(request) is True
  except Exception:return False
 # Dashboard receives the captured source snapshot, not a changing fixture list.
 captured={'observed_at':snapshot['observed_at'],'items':deepcopy(snapshot['items'])}
 gate=DashboardSnapshots({'brics_streams':lambda:deepcopy(captured)},verified=True,allowed_hosts={'brics_streams':['www.youtube.com']})
 app=create_app(authorize=strict_authorize,allowed_origin=allowed_origin,brics_stream_fixture=FixtureStreams(snapshot['items']),dashboard_snapshot_reader=gate)
 app.config['STREAM_FIXTURE_SOURCE_SHA256']=snapshot['sha256']
 return app
