"""Safe staging entrypoint. All live collection/mail/legacy routes absent."""
import os
from integration.news_api import create_app
app=create_app(branding_public_base=os.getenv("MERGED_PUBLIC_BASE_URL") or None)
