import os
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file

from app.services.report_service import (
    build_data_from_template,
    calculate_custom_metric,
    export_to_excel,
    export_to_pdf,
    list_export_logs,
    list_metric_templates,
    list_report_templates,
    save_metric_template,
    save_report_template,
    write_export_log,
)

report_tools_bp = Blueprint("report_tools", __name__, url_prefix="/api/reports")


@report_tools_bp.post("/custom-metric")
def custom_metric():
    body = request.get_json(silent=True) or {}
    expression = body.get("expression", "")
    variables = body.get("variables", {})
    value = calculate_custom_metric(expression, variables)
    return jsonify({"expression": expression, "value": value})


@report_tools_bp.post("/export")
def export_report():
    body = request.get_json(silent=True) or {}
    export_format = body.get("format", "excel")
    data = body.get("data", [])
    title = body.get("title", "运营分析报表")
    report_name = body.get("report_name", title)

    if export_format == "pdf":
        buffer = export_to_pdf(data, title=title)
        write_export_log(
            report_name=report_name,
            export_format="pdf",
            row_count=len(data),
            file_path="in-memory",
        )
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype="application/pdf",
        )

    output_dir = os.path.join(os.getcwd(), "data", "exports")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(
        output_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    export_to_excel(data, output_path)
    write_export_log(
        report_name=report_name,
        export_format="excel",
        row_count=len(data),
        file_path=output_path,
    )
    return send_file(
        output_path,
        as_attachment=True,
        download_name=os.path.basename(output_path),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@report_tools_bp.get("/metric-templates")
def metric_templates():
    return jsonify({"data": list_metric_templates()})


@report_tools_bp.post("/metric-templates")
def upsert_metric_template():
    body = request.get_json(silent=True) or {}
    return jsonify({"data": save_metric_template(body)})


@report_tools_bp.get("/report-templates")
def report_templates():
    return jsonify({"data": list_report_templates()})


@report_tools_bp.post("/report-templates")
def upsert_report_template():
    body = request.get_json(silent=True) or {}
    return jsonify({"data": save_report_template(body)})


@report_tools_bp.post("/export-by-template")
def export_by_template():
    body = request.get_json(silent=True) or {}
    template_id = body.get("template_id")
    export_format = body.get("format", "excel")
    override_filters = body.get("filters", {})
    report_name, data = build_data_from_template(template_id, override_filters=override_filters)
    title = body.get("title", report_name)

    if export_format == "pdf":
        buffer = export_to_pdf(data, title=title)
        write_export_log(
            report_name=report_name,
            export_format="pdf",
            row_count=len(data),
            file_path="in-memory",
        )
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mimetype="application/pdf",
        )

    output_dir = os.path.join(os.getcwd(), "data", "exports")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(
        output_dir, f"{report_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    export_to_excel(data, output_path)
    write_export_log(
        report_name=report_name,
        export_format="excel",
        row_count=len(data),
        file_path=output_path,
    )
    return send_file(
        output_path,
        as_attachment=True,
        download_name=os.path.basename(output_path),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@report_tools_bp.get("/export-logs")
def export_logs():
    limit = int(request.args.get("limit", 30))
    return jsonify({"data": list_export_logs(limit=limit)})
