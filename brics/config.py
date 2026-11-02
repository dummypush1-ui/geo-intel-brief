"""Central config: every feature is read from .env, everything defaults OFF/local."""
import os
from core.paths import ROOT, DATA_DIR, data_path

PKG_DIR = os.path.dirname(os.path.abspath(__file__))


def _getenv(key, default=None):
    """BRICS_<KEY> overrides <KEY>, so this app and Geo News can share one
    .env even where they need different values (SMTP_PORT, thresholds...)."""
    v = os.getenv("BRICS_" + key)
    return v if v is not None else os.getenv(key, default)


def _bool(key, default="false"):
    return _getenv(key, default).strip().lower() in ("1", "true", "yes", "on")


def _list(key, default=""):
    raw = _getenv(key, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


# ---- Deploy / storage ----
DEPLOY_MODE = _getenv("DEPLOY_MODE", "local")          # local | cloud
STORAGE_BACKEND = _getenv("STORAGE_BACKEND", "sqlite")  # sqlite | mongodb
SQLITE_PATH = str(data_path(_getenv("SQLITE_PATH", "brics.db")))
MONGODB_URI = _getenv("MONGODB_URI", "")
MONGODB_DB = _getenv("MONGODB_DB", "newsbot")

# ---- Delivery channels ----
ENABLE_EMAIL = _bool("ENABLE_EMAIL")
EMAIL_FROM = _getenv("EMAIL_FROM", "")
EMAIL_TO = _getenv("EMAIL_TO", "")
EMAIL_APP_PASSWORD = _getenv("EMAIL_APP_PASSWORD", "")
SMTP_HOST = _getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(_getenv("SMTP_PORT", "587"))

ENABLE_WHATSAPP = _bool("ENABLE_WHATSAPP")
WHATSAPP_PHONE = _getenv("WHATSAPP_PHONE", "")
WHATSAPP_APIKEY = _getenv("WHATSAPP_APIKEY", "")

ENABLE_TELEGRAM = _bool("ENABLE_TELEGRAM")
TELEGRAM_BOT_TOKEN = _getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = _getenv("TELEGRAM_CHAT_ID", "")

# ---- Schedule ----
# Tier 1 (wire agencies: TASS, RIA, Xinhua, IRNA) actually publish fast —
# worth polling often. Tier 2 (regular outlets) rarely refresh faster than
# this anyway, so polling them as often as tier 1 just burns requests/quota
# on sources that haven't changed. Kept separate so each can be tuned in
# .env without touching code.
COLLECT_INTERVAL_TIER1_MINUTES = int(_getenv("COLLECT_INTERVAL_TIER1_MINUTES", "10"))
COLLECT_INTERVAL_TIER2_MINUTES = int(_getenv("COLLECT_INTERVAL_TIER2_MINUTES", "30"))
DIGEST_TIMES = _list("DIGEST_TIMES", "09:00,20:00")

# ---- Cloud trigger security ----
TRIGGER_SECRET = os.getenv("TRIGGER_SECRET", "")  # shared; see core/auth.py

# ---- Optional features ----
ENABLE_CRITICAL_ALERTS = _bool("ENABLE_CRITICAL_ALERTS")
CRITICAL_KEYWORDS = _list("CRITICAL_KEYWORDS", "attack,explosion,resign,coup,ceasefire,sanctions")

ENABLE_WEEKLY_REPORT = _bool("ENABLE_WEEKLY_REPORT")
WEEKLY_REPORT_DAY = _getenv("WEEKLY_REPORT_DAY", "Monday")

ENABLE_DASHBOARD = _bool("ENABLE_DASHBOARD")
DASHBOARD_KEY = _getenv("DASHBOARD_KEY", "changeme")

ENABLE_TIER3_SCRAPE = _bool("ENABLE_TIER3_SCRAPE")

DEDUPE_THRESHOLD = float(_getenv("DEDUPE_THRESHOLD", "0.8"))
ACTIVE_CATEGORIES = _list("ACTIVE_CATEGORIES", "GEOPOLITICS,TRADE,SANCTIONS,RISK,CONFERENCE,GENERAL")

_sf = _getenv("SOURCES_FILE", "")
SOURCES_FILE = _sf if _sf else os.path.join(PKG_DIR, "settings", "sources.yaml")