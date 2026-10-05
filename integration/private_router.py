"""Deny-by-default preview entrypoint. No live collector or mail routes."""
import os
from integration.preview_launcher import build_preview
# Copy environment once into a plain snapshot; never mutate operator settings.
app=build_preview(dict(os.environ))
