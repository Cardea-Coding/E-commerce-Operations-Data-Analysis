from flask import Blueprint, jsonify, request

from app.services.sync_service import get_sync_logs, run_data_sync

data_sync_bp = Blueprint("data_sync", __name__, url_prefix="/api/data-sync")


@data_sync_bp.post("/run")
def run_sync():
    body = request.get_json(silent=True) or {}
    source = body.get("source", "mock_api")
    mode = body.get("mode", "manual")
    taobao_endpoint = body.get("taobao_endpoint")
    mysql_uri = body.get("mysql_uri")
    result = run_data_sync(
        source=source, mode=mode, taobao_endpoint=taobao_endpoint, mysql_uri=mysql_uri
    )
    return jsonify({"data": result})


@data_sync_bp.get("/logs")
def sync_logs():
    limit = int(request.args.get("limit", 20))
    data = get_sync_logs(limit=limit)
    return jsonify({"data": data})
