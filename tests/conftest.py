import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.update(DATA_DIR=tempfile.mkdtemp(prefix='geo-tests-'), RUN_SCHEDULER='false',
                  STORAGE_BACKEND='sqlite', MONGODB_URI='', GEO_ENABLE_TELEGRAM_BACKUP='false')
