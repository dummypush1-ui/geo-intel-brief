"""Geo Intel Brief - ONE web service:

    /            hub (status + links)
    /hsn/        Worldwide HSN Code Finder (static app + AI/ships API)
    /brics/      BRICS Live Monitor (dashboard, live video, alerts)
    /geo/        Geo Intel Monitor (trade / sanctions / research digest)
    /health      aggregate health      /api/status   detailed status
    /api/links/news-for-code?code=8542   /api/links/codes-for-article?text=...   (news <-> HS codes)
    /api/trigger/collect   POST ?key=TRIGGER_SECRET   run both collectors

Run:  gunicorn app:app   (see Procfile)    or    python app.py
"""
import logging
import os

from flask import Flask, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

from core import auth, paths  # noqa: F401  (paths loads .env first)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"),
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("hub")


def _flag(name, default="true"):
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config["JSON_SORT_KEYS"] = False
    # Render / most PaaS sit behind exactly one proxy hop.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    modules = {}   # name -> {"ok": bool, "error": str|None, "path": str, "title": str}

    def mount(name, title, prefix, importer):
        if not _flag(f"ENABLE_{name.upper()}_APP"):
            modules[name] = dict(ok=False, error="disabled by ENABLE_%s_APP=false" % name.upper(), path=prefix, title=title, disabled=True)
            return
        try:
            bp, init = importer()
            app.register_blueprint(bp, url_prefix=prefix)
            ready = init(app) if init else True
            modules[name] = dict(ok=ready is not False,
                                 error=None if ready is not False else "Initialization failed; check server configuration and logs",
                                 path=prefix + "/", title=title)
        except Exception as e:  # one broken sub-app must not take the others down
            log.exception("failed to mount %s", name)
            modules[name] = dict(ok=False, error=f"{type(e).__name__}: {e}", path=prefix + "/", title=title)

    def _hsn():
        from hsn.routes import bp, init_app
        return bp, init_app

    def _brics():
        from brics.web import bp
        from brics.database import get_store
        get_store()                      # creates the SQLite file / Mongo index up front
        return bp, None

    def _geo():
        from geonews.web import bp, init_app
        return bp, lambda a: init_app()

    mount("hsn", "HSN Code Finder", "/hsn", _hsn)
    mount("brics", "BRICS Live Monitor", "/brics", _brics)
    mount("geo", "Geo Intel Monitor", "/geo", _geo)
    app.config["MODULES"] = modules

    # news <-> HS-code link (works with whichever of the apps are up)
    try:
        from core.links import bp as links_bp
        app.register_blueprint(links_bp, url_prefix="/api/links")
    except Exception:  # noqa: BLE001
        log.exception("links blueprint failed to mount")

    @app.get("/")
    def hub():
        return render_template("hub.html", modules=modules)

    @app.get("/health")
    def health():
        ok = any(m["ok"] for m in modules.values())
        return jsonify(status="ok" if ok else "degraded",
                       apps={k: v["ok"] for k, v in modules.items()}), (200 if ok else 503)

    @app.get("/api/status")
    def status():
        if not auth.authorized():
            return auth.deny()
        from core import scheduler
        return jsonify(apps=modules, scheduler=scheduler.STATUS, collecting=scheduler.is_collecting(),
                       trigger_secret_ok=not auth.secret_is_weak())

    @app.post("/api/trigger/collect")
    def trigger_collect():
        if not auth.authorized():
            return auth.deny()
        from core import scheduler
        started = scheduler.collect_all_async(enable_brics=modules["brics"]["ok"],
                                              enable_geo=modules["geo"]["ok"])
        return jsonify(status="started" if started else "already_running"), 202

    # In-process scheduler: opt-in for gunicorn, on by default for `python app.py`.
    if _flag("RUN_SCHEDULER", "false"):
        from core import scheduler
        scheduler.start(enable_brics=modules["brics"]["ok"], enable_geo=modules["geo"]["ok"])
    return app


app = create_app()

if __name__ == "__main__":
    if os.getenv("RUN_SCHEDULER") is None:
        os.environ["RUN_SCHEDULER"] = "true"
        from core import scheduler
        scheduler.start(enable_brics=app.config["MODULES"]["brics"]["ok"], enable_geo=app.config["MODULES"]["geo"]["ok"])
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), threaded=True)
