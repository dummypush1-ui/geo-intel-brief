import os
from core.paths import ROOT, DATA_DIR, data_path

PKG_DIR = os.path.dirname(os.path.abspath(__file__))


def _getenv(key, default=None):
    """GEO_<KEY> overrides <KEY> (shared .env with BRICS)."""
    v = os.getenv("GEO_" + key)
    return v if v is not None else os.getenv(key, default)

# ---------- core ----------
MONGODB_URI = _getenv("MONGODB_URI", "")
MONGODB_DB_NAME = _getenv("MONGODB_DB_NAME", "geo_intel")
REQUEST_TIMEOUT = int(_getenv("REQUEST_TIMEOUT", "20"))
LOOKBACK_HOURS = int(_getenv("LOOKBACK_HOURS", "48"))
UPCOMING_DAYS = int(_getenv("UPCOMING_DAYS", "90"))
MAX_ITEMS_PER_FEED = int(_getenv("MAX_ITEMS_PER_FEED", "40"))
EXTRA_RSS_FEEDS = [x.strip() for x in _getenv("EXTRA_RSS_FEEDS", "").split(",") if x.strip()]

# Which categories actually get saved/emailed. The classifier still tags
# everything (GEOPOLITICS, CONFERENCE, TRADE, SANCTIONS, RISK, RESEARCH,
# GENERAL), but only categories listed here pass through into the digest.
# Default is ALL categories -- a "Global Geopolitical Intelligence" brief
# that only ever showed TRADE/SANCTIONS/RESEARCH (the old default) is why
# most cycles showed "0 relevant items": real-world RSS output skews
# GEOPOLITICS/CONFERENCE/RISK, and those were being silently filtered out
# in collectors/rss.py BEFORE anything reached MongoDB. Narrow this back
# down via the ACTIVE_CATEGORIES env var on Render if you only want a
# subset (e.g. "TRADE,SANCTIONS,RESEARCH").
ACTIVE_CATEGORIES = [c.strip().upper() for c in
                      _getenv("ACTIVE_CATEGORIES",
                                "GEOPOLITICS,CONFERENCE,TRADE,SANCTIONS,RISK,RESEARCH,GENERAL").split(",")
                      if c.strip()]

# Fuzzy near-duplicate filtering (0-1, higher = stricter match required).
# Same story reported by multiple outlets in one cycle collapses to one item.
DEDUPE_THRESHOLD = float(_getenv("DEDUPE_THRESHOLD", "0.85"))

# ---------- scheduler ----------
# 24h "HH:MM" local time, used by scheduler.py for the daily automated run.
DAILY_RUN_TIME = _getenv("DAILY_RUN_TIME", "07:00")
# Day of week the weekly summary goes out (see WEEKLY_REPORT below).
WEEKLY_REPORT_DAY = _getenv("WEEKLY_REPORT_DAY", "monday").lower()

# ---------- web trigger (Render + Apps Script) ----------
# Shared-secret so random people on the internet can't hit your Render URL
# and trigger collection/email themselves. Apps Script sends this as
# ?key=... on every request.
TRIGGER_SECRET = os.getenv("TRIGGER_SECRET", "")  # shared; see core/auth.py

# Render sets this automatically for every deployed service — used to
# build the "view full dashboard" link in Telegram/email digests.
DASHBOARD_BASE_URL = (os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL") or _getenv("DASHBOARD_BASE_URL", "")).rstrip("/")

# ---------- email (required for the daily digest) ----------
SMTP_HOST = _getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(_getenv("SMTP_PORT", "465"))
EMAIL_FROM = _getenv("EMAIL_FROM", "")
EMAIL_TO = _getenv("EMAIL_TO", "")
EMAIL_APP_PASSWORD = _getenv("EMAIL_APP_PASSWORD", "")

# ---------- feature: archive each day's digest to disk ----------
ARCHIVE_DIGESTS = _getenv("ARCHIVE_DIGESTS", "true").lower() == "true"
ARCHIVE_DIR = str(data_path(_getenv("ARCHIVE_DIR", "archive")))

# ---------- feature: instant critical-risk alert ----------
# Off by default. Sends a short separate email the moment a CRITICAL item
# appears, instead of waiting for the next scheduled daily digest.
ENABLE_CRITICAL_ALERTS = _getenv("ENABLE_CRITICAL_ALERTS", "false").lower() == "true"
CRITICAL_ALERT_LOOKBACK_HOURS = int(_getenv("CRITICAL_ALERT_LOOKBACK_HOURS", "6"))

# ---------- feature: weekly trend summary ----------
# Off by default. Sends a rollup (top stories, category/country breakdown)
# once a week on WEEKLY_REPORT_DAY at DAILY_RUN_TIME.
ENABLE_WEEKLY_REPORT = _getenv("ENABLE_WEEKLY_REPORT", "false").lower() == "true"

# ---------- optional: full-article-text extraction ----------
# Off by default: slow, and many sites block scraping. RSS summaries are
# used when this is disabled.
ENABLE_FULL_TEXT = _getenv("ENABLE_FULL_TEXT", "false").lower() == "true"
FULL_TEXT_MAX_CHARS = int(_getenv("FULL_TEXT_MAX_CHARS", "700"))
FULL_TEXT_WORKERS = int(_getenv("FULL_TEXT_WORKERS", "5"))

# ---------- optional: Google News keyword collector ----------
# Off by default. Turn on with ENABLE_GNEWS=true in .env.
ENABLE_GNEWS = _getenv("ENABLE_GNEWS", "false").lower() == "true"
GNEWS_LANGUAGE = _getenv("GNEWS_LANGUAGE", "en")
GNEWS_COUNTRY = _getenv("GNEWS_COUNTRY", "US")
GNEWS_PERIOD = _getenv("GNEWS_PERIOD", "1d")
GNEWS_MAX_RESULTS = int(_getenv("GNEWS_MAX_RESULTS", "15"))
# Boolean-OR keyword groups. Commas alone do NOT mean OR to Google News --
# each group below is joined with " OR " before the query is sent.
# Focused on trade activity + sanctions/circulars/notifications + research.
GNEWS_QUERY_GROUPS = [
    ["tariff", "trade war", "export control", "FTA", "trade order",
     "trade policy", "trade risk", "international trade"],
    ["sanctions", "embargo", "circular", "notification", "foreign policy",
     "export ban", "import ban"],
    ["research paper", "policy brief", "working paper", "white paper", "report published"],
]

# ---------- optional: WhatsApp digest via CallMeBot ----------
# Off by default. Turn on with ENABLE_WHATSAPP=true in .env.
ENABLE_WHATSAPP = _getenv("ENABLE_WHATSAPP", "false").lower() == "true"
WHATSAPP_PHONE = _getenv("WHATSAPP_PHONE", "")
WHATSAPP_APIKEY = _getenv("WHATSAPP_APIKEY", "")

# ---------- optional: Telegram digest ----------
# Off by default. More reliable than CallMeBot/WhatsApp (official Bot API,
# no per-message manual re-verification). Turn on with ENABLE_TELEGRAM=true.
# Setup: message @BotFather to create a bot and get TELEGRAM_BOT_TOKEN, then
# message your bot once and fetch TELEGRAM_CHAT_ID from
# https://api.telegram.org/bot<token>/getUpdates
ENABLE_TELEGRAM = _getenv("ENABLE_TELEGRAM", "false").lower() == "true"
TELEGRAM_BOT_TOKEN = _getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = _getenv("TELEGRAM_CHAT_ID", "")

# ---------- Telegram = full data storage (every article, in full) ----------
# This is now the primary full-content store. MongoDB only keeps lightweight
# metadata (title, score, category, short preview, and a link back to the
# full Telegram message) — the complete record (full summary/extracted
# text, all fields) is posted to a dedicated Telegram channel via your bot
# at collection time, once per collection cycle (batched, to stay well
# under Telegram's rate limits rather than one message per article).
# Uses the same bot as ENABLE_TELEGRAM above by default; set
# TELEGRAM_BACKUP_BOT_TOKEN separately only if you want a different bot.
ENABLE_TELEGRAM_BACKUP = _getenv("ENABLE_TELEGRAM_BACKUP", "true").lower() == "true"
TELEGRAM_BACKUP_BOT_TOKEN = _getenv("TELEGRAM_BACKUP_BOT_TOKEN", "") or TELEGRAM_BOT_TOKEN
TELEGRAM_BACKUP_CHAT_ID = _getenv("TELEGRAM_BACKUP_CHAT_ID", "")

# ---------- optional: periodic Mongo metadata cleanup ----------
# Since the full record already lives permanently in the Telegram backup
# channel from the moment it's collected, old MongoDB metadata can simply
# be deleted (not re-archived) once it's no longer needed for the
# dashboard/digest — nothing is lost, the full data is already on Telegram.
ENABLE_METADATA_CLEANUP = _getenv("ENABLE_METADATA_CLEANUP", "false").lower() == "true"
METADATA_CLEANUP_AFTER_DAYS = int(_getenv("METADATA_CLEANUP_AFTER_DAYS", "60"))
