"""Read-only job diagnostic entry; set parent bound before application imports.
No live provider, URI access, schedule, credentials or write authority.
"""
import resource
LIMIT=512*1024*1024
resource.setrlimit(resource.RLIMIT_AS,(LIMIT,LIMIT))
from integration.collector197_job import main
if __name__=='__main__':raise SystemExit(main())
