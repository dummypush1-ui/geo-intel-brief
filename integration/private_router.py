"""Deny-by-default preview entrypoint. No live collector or mail routes."""
import os
from integration.preview_launcher import build_preview
# Copy environment once into a plain snapshot; never mutate operator settings.
environment=dict(os.environ)
factory=None
if environment.get("PREVIEW_GEO_ONLY_ENABLED","false")=="true" and environment.get("NEWS_READ_ENABLED","false")=="true":
 from integration.geo_read_factory import create_geo_read_client
 factory=create_geo_read_client
app=build_preview(environment,client_factory=factory)
