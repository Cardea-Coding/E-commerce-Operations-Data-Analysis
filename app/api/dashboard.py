from flask import Blueprint, jsonify, request

from app.services.cache_service import get_cache, set_cache
from app.services.data_service import (
    get_dashboard_dimensions,
    get_dashboard_drilldown,
    get_dashboard_overview,
    get_dashboard_trend,
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.get("/overview")
def dashboard_overview():
    params = request.args.to_dict()
    cache_key = f"dashboard:overview:{params}"
    cached = get_cache(cache_key)
    if cached:
        return jsonify({"source": "cache", "data": cached})

    data = get_dashboard_overview(
        start_time=params.get("start_time"),
        end_time=params.get("end_time"),
        region=params.get("region"),
        category=params.get("category"),
        campaign_id=params.get("campaign_id"),
    )
    set_cache(cache_key, data, ttl=60)
    return jsonify({"source": "db", "data": data})


@dashboard_bp.get("/trend")
def dashboard_trend():
    params = request.args.to_dict()
    data = get_dashboard_trend(
        granularity=params.get("granularity", "day"),
        start_time=params.get("start_time"),
        end_time=params.get("end_time"),
        region=params.get("region"),
        category=params.get("category"),
        campaign_id=params.get("campaign_id"),
    )
    return jsonify({"data": data})


@dashboard_bp.get("/dimensions")
def dashboard_dimensions():
    data = get_dashboard_dimensions()
    return jsonify({"data": data})


@dashboard_bp.get("/drilldown")
def dashboard_drilldown():
    params = request.args.to_dict()
    data = get_dashboard_drilldown(
        start_time=params.get("start_time"),
        end_time=params.get("end_time"),
        region=params.get("region"),
        category=params.get("category"),
        campaign_id=params.get("campaign_id"),
    )
    return jsonify({"data": data})