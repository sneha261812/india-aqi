"""
India AQI Intelligence Platform — Flask Backend
app.py — hardened startup: /ping registers FIRST, blueprints are defensive
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")

    # ── CORS ───────────────────────────────────────────────────────────────
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://india-aqi-gamma.vercel.app",
        "https://india-aqi.vercel.app",
    ]
    env_origin = os.getenv("FRONTEND_URL", "").strip()
    if env_origin and env_origin not in allowed_origins:
        allowed_origins.append(env_origin)
    CORS(app, origins=allowed_origins, supports_credentials=True)

    # ── /ping FIRST — before any blueprint or scheduler import ─────────────
    # This guarantees cron-job.org and Render health checks always succeed
    # even if a blueprint has an import error.
    @app.route("/ping", methods=["GET"])
    def ping():
        return jsonify({"status": "ok", "service": "india-aqi-backend"}), 200

    @app.route("/", methods=["GET"])
    def root():
        return jsonify({"status": "ok", "service": "india-aqi-backend"}), 200

    # ── Error handlers ─────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Internal error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    # ── Blueprints — wrapped so one bad import can't kill /ping ───────────
    blueprints = [
        ("routes.aqi_routes",      "aqi_bp",      "/api/aqi"),
        ("routes.forecast_routes", "forecast_bp", "/api/forecast"),
        ("routes.chatbot_routes",  "chatbot_bp",  "/api/chat"),
        ("routes.health_routes",   "health_bp",   "/api/health"),
        ("routes.device_routes",   "device_bp",   "/api/devices"),
        ("routes.state_routes",    "state_bp",    "/api/states"),
    ]
    for module_name, bp_name, prefix in blueprints:
        try:
            import importlib
            module = importlib.import_module(module_name)
            bp = getattr(module, bp_name)
            app.register_blueprint(bp, url_prefix=prefix)
            logger.info(f"✅ Blueprint registered: {prefix}")
        except Exception as exc:
            logger.error(f"❌ Blueprint FAILED ({module_name}): {exc}")
            # App continues — /ping still works even if this blueprint fails

    # ── Scheduler — wrapped so it can't crash the app ─────────────────────
    try:
        from scheduler import init_scheduler
        init_scheduler(app)
        logger.info("✅ Scheduler started")
    except Exception as exc:
        logger.error(f"❌ Scheduler failed to start: {exc}")

    logger.info("✅ India AQI backend ready")
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
