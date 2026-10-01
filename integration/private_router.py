"""Deny-by-default preview entrypoint. No live collector or mail routes."""
import os
from integration.runtime import compose
app=compose(os.environ)
