import ast
import io
import json

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.extensions import db
from app.models import ExportLog, MetricTemplate, ReportTemplate
from app.services.data_service import (
    get_dashboard_overview,
    get_marketing_effectiveness,
    get_product_diagnosis,
    get_user_segments,
)

class SafeExpressionEvaluator(ast.NodeVisitor):
    allowed_nodes = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.Pow,
        ast.USub,
        ast.Name,
        ast.Load,
        ast.Constant,
    )

    def __init__(self, variables):
        self.variables = variables

    def visit(self, node):
        if not isinstance(node, self.allowed_nodes):
            raise ValueError("表达式包含不支持的语法")
        return super().visit(node)

    def evaluate(self, expression):
        tree = ast.parse(expression, mode="eval")
        return self.visit(tree.body)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right if right else 0
        if isinstance(node.op, ast.Mod):
            return left % right if right else 0
        if isinstance(node.op, ast.Pow):
            return left**right
        raise ValueError("不支持的运算符")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        raise ValueError("不支持的一元运算")

    def visit_Name(self, node):
        if node.id not in self.variables:
            raise ValueError(f"未知变量: {node.id}")
        return self.variables[node.id]

    def visit_Constant(self, node):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("仅支持数字常量")


def calculate_custom_metric(expression, variables):
    evaluator = SafeExpressionEvaluator(variables)
    return round(float(evaluator.evaluate(expression)), 4)


def export_to_excel(data, output_path):
    df = pd.DataFrame(data)
    df.to_excel(output_path, index=False)
    return output_path


def export_to_pdf(data, title="运营分析报表"):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, y, title)
    y -= 24
    p.setFont("Helvetica", 10)
    for row in data:
        line = " | ".join([f"{k}: {v}" for k, v in row.items()])
        if y < 40:
            p.showPage()
            y = height - 40
            p.setFont("Helvetica", 10)
        p.drawString(40, y, line[:120])
        y -= 16
    p.save()
    buffer.seek(0)
    return buffer


def save_metric_template(payload):
    template_id = payload.get("id")
    if template_id:
        model = db.session.get(MetricTemplate, int(template_id))
        if not model:
            raise ValueError("metric template not found")
    else:
        model = MetricTemplate(name=payload["name"])
        db.session.add(model)
    model.name = payload.get("name", model.name)
    model.expression = payload["expression"]
    model.variables_schema = json.dumps(payload.get("variables_schema", []), ensure_ascii=False)
    model.description = payload.get("description")
    db.session.commit()
    return {"id": model.id}


def list_metric_templates():
    rows = db.session.query(MetricTemplate).order_by(MetricTemplate.id.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "expression": r.expression,
            "variables_schema": json.loads(r.variables_schema or "[]"),
            "description": r.description,
        }
        for r in rows
    ]


def save_report_template(payload):
    template_id = payload.get("id")
    if template_id:
        model = db.session.get(ReportTemplate, int(template_id))
        if not model:
            raise ValueError("report template not found")
    else:
        model = ReportTemplate(name=payload["name"], query_type=payload["query_type"])
        db.session.add(model)
    model.name = payload.get("name", model.name)
    model.query_type = payload.get("query_type", model.query_type)
    model.filters_json = json.dumps(payload.get("filters", {}), ensure_ascii=False)
    model.columns_json = json.dumps(payload.get("columns", []), ensure_ascii=False)
    db.session.commit()
    return {"id": model.id}


def list_report_templates():
    rows = db.session.query(ReportTemplate).order_by(ReportTemplate.id.desc()).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "query_type": r.query_type,
            "filters": json.loads(r.filters_json or "{}"),
            "columns": json.loads(r.columns_json or "[]"),
        }
        for r in rows
    ]


def build_data_from_template(template_id, override_filters=None):
    tpl = db.session.get(ReportTemplate, int(template_id))
    if not tpl:
        raise ValueError("report template not found")
    filters = json.loads(tpl.filters_json or "{}")
    if override_filters:
        filters.update(override_filters)
    query_type = tpl.query_type

    if query_type == "dashboard":
        payload = get_dashboard_overview(**filters)
        data = [payload.get("metrics", {})]
    elif query_type == "marketing":
        payload = get_marketing_effectiveness(**filters)
        data = payload.get("campaigns", [])
    elif query_type == "user":
        payload = get_user_segments(**filters)
        data = payload.get("sample_users", [])
    elif query_type == "product":
        payload = get_product_diagnosis(**filters)
        data = payload.get("high_profit_products", [])
    else:
        raise ValueError("unsupported query_type")

    columns = json.loads(tpl.columns_json or "[]")
    if columns:
        data = [{k: row.get(k) for k in columns} for row in data]
    return tpl.name, data


def write_export_log(report_name, export_format, row_count, file_path, status="success"):
    log = ExportLog(
        report_name=report_name,
        export_format=export_format,
        row_count=row_count,
        file_path=file_path,
        status=status,
    )
    db.session.add(log)
    db.session.commit()
    return log.id


def list_export_logs(limit=30):
    rows = db.session.query(ExportLog).order_by(ExportLog.id.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "report_name": r.report_name,
            "export_format": r.export_format,
            "row_count": r.row_count,
            "file_path": r.file_path,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]