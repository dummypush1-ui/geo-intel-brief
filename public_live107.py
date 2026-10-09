"""WSGI entry only. Reusable builders live in side-effect-free composition."""
import os
from integration.public_live_builder import *
app=guarded_public_app(dict(os.environ))
