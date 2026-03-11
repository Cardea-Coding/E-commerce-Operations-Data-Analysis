from flask import Blueprint, jsonify, request

from app.services.data_service import get_marketing_effectiveness

marketing_analysis_bp = Blueprint("marketing_analysis", __name__, url_prefix="/api/marketing")


@marketing_analysis_bp.get("/effectiveness")
def marketing_effectiveness():
    params = request.args.to_dict()
    data = get_marketing_effectiveness(
        start_time=params.get("start_time"),
        end_time=params.get("end_time"),
        campaign_id=params.get("campaign_id"),
    )
    return jsonify({"data": data})
