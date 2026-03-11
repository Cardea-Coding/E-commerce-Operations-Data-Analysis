import time

from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Order, Product, User, UserBehavior
from app.services.cache_service import get_cache_stats, reset_cache_stats
from app.services.data_service import get_dashboard_overview

system_monitor_bp = Blueprint("system_monitor", __name__, url_prefix="/api/system")


@system_monitor_bp.get("/perf-summary")
def perf_summary():
    t0 = time.perf_counter()
    _ = get_dashboard_overview()
    overview_ms = round((time.perf_counter() - t0) * 1000, 2)
    return jsonify(
        {
            "data": {
                "cache": get_cache_stats(),
                "database_counts": {
                    "users": db.session.query(User).count(),
                    "products": db.session.query(Product).count(),
                    "orders": db.session.query(Order).count(),
                    "behaviors": db.session.query(UserBehavior).count(),
                },
                "api_latency_ms": {
                    "dashboard_overview_single_call": overview_ms,
                },
            }
        }
    )


@system_monitor_bp.post("/cache-reset")
def cache_reset():
    reset_cache_stats()
    return jsonify({"data": {"status": "ok"}})
