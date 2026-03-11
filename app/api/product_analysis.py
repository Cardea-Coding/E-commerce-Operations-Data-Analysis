from flask import Blueprint, jsonify, request

from app.services.data_service import get_product_diagnosis

product_analysis_bp = Blueprint("product_analysis", __name__, url_prefix="/api/products")


@product_analysis_bp.get("/diagnosis")
def product_diagnosis():
    params = request.args.to_dict()
    data = get_product_diagnosis(
        start_time=params.get("start_time"),
        end_time=params.get("end_time"),
        category=params.get("category"),
    )
    return jsonify({"data": data})