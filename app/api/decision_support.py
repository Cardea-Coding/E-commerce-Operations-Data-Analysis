from flask import Blueprint, jsonify, request

from app.services.data_service import (
    get_decision_rules,
    get_decision_suggestions,
    save_decision_rule,
)

decision_support_bp = Blueprint("decision_support", __name__, url_prefix="/api/decision")


@decision_support_bp.get("/suggestions")
def decision_suggestions():
    data = get_decision_suggestions()
    return jsonify({"data": data})


@decision_support_bp.get("/rules")
def decision_rules():
    data = get_decision_rules()
    return jsonify({"data": data})


@decision_support_bp.post("/rules")
def upsert_rule():
    body = request.get_json(silent=True) or {}
    data = save_decision_rule(body)
    return jsonify({"data": data})
