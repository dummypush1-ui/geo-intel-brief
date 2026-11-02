"""Single place that decides where files live, so nothing depends on the
process working directory (the three original projects all did)."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")          # one .env for the whole service

DATA_DIR = Path(os.getenv("DATA_DIR", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)


def data_path(*parts, default_rel=None):
    """Resolve a user-supplied path: absolute stays absolute, relative is
    anchored to DATA_DIR."""
    p = Path(os.path.join(*parts)) if parts else Path(default_rel or "")
    return p if p.is_absolute() else DATA_DIR / p
