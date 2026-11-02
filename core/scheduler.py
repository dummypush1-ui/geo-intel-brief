"""One background scheduler for both news apps (replaces brics/scheduler.py,
brics/run_all.py and geonews/scheduler.py). Uses its own schedule.Scheduler
instance so nothing else in the process can interfere with the jobs."""
import logging
import threading
import time
from datetime import datetime, timezone

import schedule

log = logging.getLogger("scheduler")

STATUS = {"started": False, "jobs": {}}
_lock = threading.Lock()
_sched = schedule.Scheduler()


def _record(name, ok, detail=""):
    STATUS["jobs"][name] = {"ok": ok, "at": datetime.now(timezone.utc).isoformat(), "detail": str(detail)[:300]}


def _guard(name):
    """Decorator: log + record, never let one job kill the scheduler loop."""
    def deco(fn):
        def run(*a, **kw):
            try:
                res = fn(*a, **kw)
                _record(name, True, res if res is not None else "")
                return res
            except Exception as e:  # noqa: BLE001
                log.exception("job %s failed", name)
                _record(name, False, e)
        run.__name__ = fn.__name__
        return run
    return deco


# ------------------------------------------------------------------ BRICS jobs
@_guard("brics.collect.tier1")
def brics_tier1():
    from brics.app import cmd_collect
    return f"{len(cmd_collect(tiers=(1,), include_official=False))} new"


@_guard("brics.collect.tier2")
def brics_tier2():
    from brics.app import cmd_collect
    return f"{len(cmd_collect(tiers=(2,), include_official=True))} new"


@_guard("brics.report")
def brics_report():
    from brics.app import cmd_report
    cmd_report()


# ------------------------------------------------------------------ Geo jobs
def _retry(name, fn, attempts=3, delay=30):
    for i in range(1, attempts + 1):
        try:
            fn()
            return True
        except Exception:  # noqa: BLE001
            log.exception("%s failed (attempt %d/%d)", name, i, attempts)
            if i < attempts:
                time.sleep(delay)
    return False


def geo_collect():
    """RSS + optional Google News + events (no sending)."""
    from geonews import config as G
    from geonews.collectors.rss import collect as collect_rss
    from geonews.collectors.events import seed_events
    from geonews.database import init_db
    init_db()
    out = {"rss": collect_rss(G.EXTRA_RSS_FEEDS)}
    if G.ENABLE_GNEWS:
        from geonews.collectors.gnews_search import collect as collect_gnews
        out["gnews"] = collect_gnews()
    out["events"] = seed_events()
    return out


@_guard("geo.daily")
def geo_daily():
    """Same order as the original run_daily_cycle: collect -> critical alert ->
    email (with retries) -> WhatsApp / Telegram."""
    from geonews import config as G
    from geonews.reports.email_report import send as send_email
    out = geo_collect()
    if G.ENABLE_CRITICAL_ALERTS:
        from geonews.reports.critical_alert import send_if_critical
        send_if_critical()
    if G.EMAIL_FROM and G.EMAIL_TO and G.EMAIL_APP_PASSWORD:
        _retry("geo daily email", send_email)
    if G.ENABLE_WHATSAPP:
        from geonews.reports.whatsapp_report import send as send_whatsapp
        send_whatsapp()
    if G.ENABLE_TELEGRAM:
        from geonews.reports.telegram_report import send as send_telegram
        send_telegram()
    return out


@_guard("geo.weekly")
def geo_weekly():
    from geonews.reports.weekly_report import send as send_weekly
    _retry("geo weekly email", send_weekly)


# ------------------------------------------------------------------ loop
def _loop():
    while True:
        try:
            _sched.run_pending()
        except Exception:  # noqa: BLE001
            log.exception("scheduler loop error (continuing)")
        time.sleep(30)


def start(enable_brics=True, enable_geo=True):
    """Idempotent. Call once per process (run gunicorn with ONE worker)."""
    with _lock:
        if STATUS["started"]:
            return False
        STATUS["started"] = True
    if enable_brics:
        from brics import config as B
        _sched.every(B.COLLECT_INTERVAL_TIER1_MINUTES).minutes.do(brics_tier1)
        _sched.every(B.COLLECT_INTERVAL_TIER2_MINUTES).minutes.do(brics_tier2)
        for t in B.DIGEST_TIMES:
            _sched.every().day.at(t).do(brics_report)
    if enable_geo:
        from geonews import config as G
        _sched.every().day.at(G.DAILY_RUN_TIME).do(geo_daily)
        if G.ENABLE_WEEKLY_REPORT:
            getattr(_sched.every(), G.WEEKLY_REPORT_DAY, _sched.every().monday).at(G.DAILY_RUN_TIME).do(geo_weekly)

    def boot():
        time.sleep(20)                       # let the web server come up first
        if enable_brics:
            brics_tier1(); brics_tier2()
    threading.Thread(target=boot, daemon=True, name="sched-boot").start()
    threading.Thread(target=_loop, daemon=True, name="scheduler").start()
    log.info("scheduler started (brics=%s geo=%s)", enable_brics, enable_geo)
    return True


# ------------------------------------------------------------------ on-demand (external cron / manual)
_run_lock = threading.Lock()
_running = {"collect": False}


def collect_all_async():
    """Kick off a full collection in a background thread; returns False if one
    is already running. Used by POST /api/trigger/collect so ONE external cron
    job can drive both news apps."""
    with _run_lock:
        if _running["collect"]:
            return False
        _running["collect"] = True

    def work():
        try:
            for fn in (brics_tier1, brics_tier2):
                fn()
            _guard("geo.collect")(geo_collect)()
        finally:
            _running["collect"] = False
    threading.Thread(target=work, daemon=True, name="collect-all").start()
    return True


def is_collecting():
    return _running["collect"]
