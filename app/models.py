from datetime import datetime

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False, unique=True)
    age = db.Column(db.Integer, nullable=False, default=25)
    gender = db.Column(db.String(16), nullable=False, default="unknown")
    region = db.Column(db.String(64), nullable=False, default="未知")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    cost = db.Column(db.Float, nullable=False, default=0.0)
    stock = db.Column(db.Integer, nullable=False, default=0)
    rating = db.Column(db.Float, nullable=False, default=5.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class MarketingCampaign(db.Model):
    __tablename__ = "marketing_campaigns"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    campaign_type = db.Column(db.String(64), nullable=False, default="promotion")
    cost = db.Column(db.Float, nullable=False, default=0.0)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(64), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    campaign_id = db.Column(
        db.Integer, db.ForeignKey("marketing_campaigns.id"), nullable=True, index=True
    )
    coupon_type = db.Column(db.String(64), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    payment_status = db.Column(db.String(16), nullable=False, default="paid")
    refund_status = db.Column(db.String(16), nullable=False, default="none")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class UserBehavior(db.Model):
    __tablename__ = "user_behaviors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    behavior_type = db.Column(db.String(32), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    product_id = db.Column(
        db.Integer, db.ForeignKey("products.id"), nullable=False, index=True
    )
    score = db.Column(db.Integer, nullable=False, default=5)
    tags = db.Column(db.String(255), nullable=True)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class CouponUsage(db.Model):
    __tablename__ = "coupon_usages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    campaign_id = db.Column(
        db.Integer, db.ForeignKey("marketing_campaigns.id"), nullable=True, index=True
    )
    coupon_type = db.Column(db.String(64), nullable=False)
    discount_amount = db.Column(db.Float, nullable=False, default=0.0)
    used = db.Column(db.Boolean, nullable=False, default=False)
    amount_before = db.Column(db.Float, nullable=False, default=0.0)
    amount_after = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)


class AdPerformance(db.Model):
    __tablename__ = "ad_performance"

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(
        db.Integer, db.ForeignKey("marketing_campaigns.id"), nullable=False, index=True
    )
    stat_date = db.Column(db.Date, nullable=False, index=True)
    clicks = db.Column(db.Integer, nullable=False, default=0)
    cost = db.Column(db.Float, nullable=False, default=0.0)
    conversions = db.Column(db.Integer, nullable=False, default=0)
    gmv = db.Column(db.Float, nullable=False, default=0.0)


class DataSyncLog(db.Model):
    __tablename__ = "data_sync_logs"

    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(64), nullable=False, index=True)
    mode = db.Column(db.String(16), nullable=False, default="manual")
    status = db.Column(db.String(16), nullable=False, default="success", index=True)
    inserted_users = db.Column(db.Integer, nullable=False, default=0)
    inserted_products = db.Column(db.Integer, nullable=False, default=0)
    inserted_orders = db.Column(db.Integer, nullable=False, default=0)
    inserted_behaviors = db.Column(db.Integer, nullable=False, default=0)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)
    message = db.Column(db.String(255), nullable=True)


class DecisionRule(db.Model):
    __tablename__ = "decision_rules"

    id = db.Column(db.Integer, primary_key=True)
    rule_key = db.Column(db.String(64), nullable=False, unique=True)
    rule_name = db.Column(db.String(128), nullable=False)
    rule_type = db.Column(db.String(32), nullable=False)  # user/product/marketing
    threshold_value = db.Column(db.Float, nullable=False, default=0.0)
    action_text = db.Column(db.String(255), nullable=False)
    reason_template = db.Column(db.String(255), nullable=False)
    priority_weight = db.Column(db.Integer, nullable=False, default=50)  # 1-100
    enabled = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MetricTemplate(db.Model):
    __tablename__ = "metric_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    expression = db.Column(db.String(255), nullable=False)
    variables_schema = db.Column(db.Text, nullable=False, default="[]")
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ReportTemplate(db.Model):
    __tablename__ = "report_templates"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    query_type = db.Column(db.String(64), nullable=False)  # dashboard/marketing/user/product
    filters_json = db.Column(db.Text, nullable=False, default="{}")
    columns_json = db.Column(db.Text, nullable=False, default="[]")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class ExportLog(db.Model):
    __tablename__ = "export_logs"

    id = db.Column(db.Integer, primary_key=True)
    report_name = db.Column(db.String(128), nullable=False)
    export_format = db.Column(db.String(16), nullable=False)
    row_count = db.Column(db.Integer, nullable=False, default=0)
    file_path = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="success")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)