"""Safe staging entrypoint. All live collection/mail/legacy routes absent."""
from integration.news_api import create_app
app=create_app()
