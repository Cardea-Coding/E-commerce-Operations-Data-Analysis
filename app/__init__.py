from flask import Flask, jsonify, render_template

from config import Config

from .api.dashboard import dashboard_bp
from .api.data_sync import data_sync_bp
from .api.decision_support import decision_support_bp
from .api.marketing_analysis import marketing_analysis_bp
from .api.product_analysis import product_analysis_bp
from .api.report_tools import report_tools_bp
from .api.system_monitor import system_monitor_bp
from .api.user_analysis import user_analysis_bp
from .extensions import db
from .services.sync_service import run_data_sync


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    register_blueprints(app)
    register_commands(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/")
    def index():
        return render_template("index.html")

    return app


def register_blueprints(app):
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(data_sync_bp)
    app.register_blueprint(user_analysis_bp)
    app.register_blueprint(product_analysis_bp)
    app.register_blueprint(marketing_analysis_bp)
    app.register_blueprint(decision_support_bp)
    app.register_blueprint(report_tools_bp)
    app.register_blueprint(system_monitor_bp)


def register_commands(app):
    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Database tables created.")

    @app.cli.command("sync-data")
    def sync_data():
        result = run_data_sync(source="mock_api", mode="manual")
        print(result)