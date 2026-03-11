from flask import Blueprint, jsonify, request

from app.services.data_service import get_user_segments

user_analysis_bp = Blueprint("user_analysis", __name__, url_prefix="/api/users")


@user_analysis_bp.get("/segments")
def user_segments():
    params = request.args.to_dict()
    data = get_user_segments(
        start_time=params.get("start_time"),
        end_time=params.get("end_time"),
        region=params.get("region"),
    )
    return jsonify({"data": data})