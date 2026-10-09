"""Public sample WSGI entry only; reusable builder has no app on import."""
import os
from integration.public_preview_builder import *
app=build_public_preview(dict(os.environ))
