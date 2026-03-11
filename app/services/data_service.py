from datetime import timedelta

import pandas as pd
from sqlalchemy import and_, func

from app.extensions import db
from app.models import (
    DecisionRule,
    AdPerformance,
    CouponUsage,
    MarketingCampaign,
    Order,
    Product,
    Review,
    User,
    UserBehavior,
)
from app.utils.helpers import safe_divide, time_range_or_default


def _base_order_query(start_dt, end_dt, region=None, category=None, campaign_id=None):
    query = (
        db.session.query(Order, User, Product)
        .join(User, User.id == Order.user_id)
        .join(Product, Product.id == Order.product_id)
        .filter(Order.created_at >= start_dt, Order.created_at <= end_dt)
    )
    if region:
        query = query.filter(User.region == region)
    if category:
        query = query.filter(Product.category == category)
    if campaign_id:
        query = query.filter(Order.campaign_id == int(campaign_id))
    return query


def get_dashboard_overview(
    start_time=None, end_time=None, region=None, category=None, campaign_id=None, window_days=30
):
    start_dt, end_dt = time_range_or_default(start_time, end_time, window_days=window_days)
    rows = _base_order_query(start_dt, end_dt, region, category, campaign_id).all()

    paid_orders = [r[0] for r in rows if r[0].payment_status == "paid" and r[0].refund_status != "full"]
    gmv = round(sum(o.amount for o in paid_orders), 2)
    order_count = len(paid_orders)

    behavior_query = (
        db.session.query(func.count(UserBehavior.id))
        .join(User, User.id == UserBehavior.user_id)
        .join(Product, Product.id == UserBehavior.product_id)
        .filter(
            UserBehavior.behavior_type == "view",
            UserBehavior.created_at >= start_dt,
            UserBehavior.created_at <= end_dt,
        )
    )
    if region:
        behavior_query = behavior_query.filter(User.region == region)
    if category:
        behavior_query = behavior_query.filter(Product.category == category)
    if campaign_id:
        behavior_query = behavior_query.filter(
            UserBehavior.product_id.in_(
                db.session.query(Order.product_id).filter(Order.campaign_id == int(campaign_id))
            )
        )
    view_count = behavior_query.scalar() or 0

    pay_conversion = round(safe_divide(order_count, view_count) * 100, 2)
    aov = round(safe_divide(gmv, order_count), 2) if order_count else 0.0

    # 与上一个同等窗口对比，做异常预警
    previous_start = start_dt - (end_dt - start_dt)
    previous_end = start_dt
    prev_rows = _base_order_query(previous_start, previous_end, region, category, campaign_id).all()
    prev_paid = [r[0] for r in prev_rows if r[0].payment_status == "paid" and r[0].refund_status != "full"]
    prev_order_count = len(prev_paid)

    prev_view_query = (
        db.session.query(func.count(UserBehavior.id))
        .join(User, User.id == UserBehavior.user_id)
        .join(Product, Product.id == UserBehavior.product_id)
        .filter(
            UserBehavior.behavior_type == "view",
            UserBehavior.created_at >= previous_start,
            UserBehavior.created_at <= previous_end,
        )
    )
    if region:
        prev_view_query = prev_view_query.filter(User.region == region)
    if category:
        prev_view_query = prev_view_query.filter(Product.category == category)
    if campaign_id:
        prev_view_query = prev_view_query.filter(
            UserBehavior.product_id.in_(
                db.session.query(Order.product_id).filter(Order.campaign_id == int(campaign_id))
            )
        )
    prev_view_count = prev_view_query.scalar() or 0
    prev_conversion = round(safe_divide(prev_order_count, prev_view_count) * 100, 2)

    alerts = []
    if prev_conversion > 0 and pay_conversion <= prev_conversion * 0.5:
        alerts.append(
            {
                "type": "conversion_drop",
                "message": f"支付转化率较上一周期下降超过50%（{prev_conversion}% -> {pay_conversion}%）",
            }
        )

    return {
        "time_range": {"start": start_dt.isoformat(), "end": end_dt.isoformat()},
        "filters": {"region": region, "category": category, "campaign_id": campaign_id},
        "metrics": {
            "gmv": gmv,
            "order_count": order_count,
            "view_count": view_count,
            "pay_conversion_rate": pay_conversion,
            "avg_order_value": aov,
        },
        "alerts": alerts,
    }


def get_dashboard_trend(
    granularity="day", start_time=None, end_time=None, region=None, category=None, campaign_id=None
):
    start_dt, end_dt = time_range_or_default(start_time, end_time, window_days=30)
    rows = _base_order_query(start_dt, end_dt, region, category, campaign_id).all()
    data = [
        {
            "created_at": r[0].created_at,
            "amount": r[0].amount if r[0].payment_status == "paid" and r[0].refund_status != "full" else 0,
            "is_paid": 1 if r[0].payment_status == "paid" and r[0].refund_status != "full" else 0,
        }
        for r in rows
    ]
    if not data:
        return []

    df = pd.DataFrame(data)
    if granularity == "hour":
        df["bucket"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d %H:00")
    elif granularity == "week":
        df["bucket"] = pd.to_datetime(df["created_at"]).dt.to_period("W").astype(str)
    else:
        df["bucket"] = pd.to_datetime(df["created_at"]).dt.strftime("%Y-%m-%d")

    agg = (
        df.groupby("bucket")
        .agg(gmv=("amount", "sum"), order_count=("is_paid", "sum"))
        .reset_index()
        .sort_values("bucket")
    )
    return agg.to_dict(orient="records")


def get_dashboard_dimensions():
    regions = [x[0] for x in db.session.query(User.region).distinct().order_by(User.region).all()]
    categories = [
        x[0] for x in db.session.query(Product.category).distinct().order_by(Product.category).all()
    ]
    campaigns = [
        {"id": c.id, "name": c.name}
        for c in db.session.query(MarketingCampaign.id, MarketingCampaign.name)
        .order_by(MarketingCampaign.id.desc())
        .all()
    ]
    return {"regions": regions, "categories": categories, "campaigns": campaigns}


def get_dashboard_drilldown(start_time=None, end_time=None, region=None, category=None, campaign_id=None):
    start_dt, end_dt = time_range_or_default(start_time, end_time, window_days=30)
    rows = _base_order_query(start_dt, end_dt, region, category, campaign_id).all()
    if not rows:
        return {"by_region": [], "by_category": [], "by_campaign": []}

    df = pd.DataFrame(
        [
            {
                "region": u.region,
                "category": p.category,
                "campaign_id": o.campaign_id,
                "amount": o.amount if o.payment_status == "paid" and o.refund_status != "full" else 0,
            }
            for o, u, p in rows
        ]
    )
    by_region = (
        df.groupby("region", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "gmv"})
        .sort_values("gmv", ascending=False)
        .to_dict(orient="records")
    )
    by_category = (
        df.groupby("category", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "gmv"})
        .sort_values("gmv", ascending=False)
        .to_dict(orient="records")
    )
    by_campaign = (
        df.groupby("campaign_id", as_index=False)["amount"]
        .sum()
        .rename(columns={"amount": "gmv"})
        .sort_values("gmv", ascending=False)
        .to_dict(orient="records")
    )
    return {"by_region": by_region, "by_category": by_category, "by_campaign": by_campaign}


def get_user_segments(start_time=None, end_time=None, region=None):
    start_dt, end_dt = time_range_or_default(start_time, end_time, window_days=90)

    query = (
        db.session.query(Order.user_id, Order.amount, Order.created_at, Order.coupon_type)
        .join(User, User.id == Order.user_id)
        .filter(
            Order.created_at >= start_dt,
            Order.created_at <= end_dt,
            Order.payment_status == "paid",
            Order.refund_status != "full",
        )
    )
    if region:
        query = query.filter(User.region == region)

    rows = query.all()
    if not rows:
        return {"segments": [], "distribution": {}, "sample_users": []}

    df = pd.DataFrame(
        rows, columns=["user_id", "amount", "created_at", "coupon_type"]
    )
    latest_date = df["created_at"].max()
    rfm = (
        df.groupby("user_id")
        .agg(
            recency=("created_at", lambda x: (latest_date - x.max()).days + 1),
            frequency=("created_at", "count"),
            monetary=("amount", "sum"),
            coupon_orders=("coupon_type", lambda x: x.notna().sum()),
        )
        .reset_index()
    )

    bucket_num = min(5, max(1, len(rfm)))
    r_labels = list(range(bucket_num, 0, -1))
    fm_labels = list(range(1, bucket_num + 1))
    rfm["r_score"] = pd.qcut(
        rfm["recency"].rank(method="first"), bucket_num, labels=r_labels, duplicates="drop"
    )
    rfm["f_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), bucket_num, labels=fm_labels, duplicates="drop"
    )
    rfm["m_score"] = pd.qcut(
        rfm["monetary"].rank(method="first"), bucket_num, labels=fm_labels, duplicates="drop"
    )
    rfm["coupon_ratio"] = rfm["coupon_orders"] / rfm["frequency"]

    def segment_row(row):
        r, f, m = int(row["r_score"]), int(row["f_score"]), int(row["m_score"])
        coupon_ratio = row["coupon_ratio"]
        if r >= 4 and f >= 4 and m >= 4:
            return "高价值用户"
        if r >= 4 and f >= 3 and m >= 2:
            return "潜力用户"
        if r >= 4 and f <= 2:
            return "新客用户"
        if coupon_ratio >= 0.7 and m <= 3:
            return "价格敏感用户"
        if r <= 2 and f >= 3:
            return "流失风险用户"
        return "一般维系用户"

    rfm["segment"] = rfm.apply(segment_row, axis=1)
    distribution = rfm["segment"].value_counts().to_dict()
    sample_users = rfm.sort_values(["segment", "monetary"], ascending=[True, False]).head(20)

    return {
        "segments": rfm.to_dict(orient="records"),
        "distribution": distribution,
        "sample_users": sample_users.to_dict(orient="records"),
    }


def get_product_diagnosis(start_time=None, end_time=None, category=None):
    start_dt, end_dt = time_range_or_default(start_time, end_time, window_days=30)
    query = (
        db.session.query(Order, Product)
        .join(Product, Product.id == Order.product_id)
        .filter(
            Order.created_at >= start_dt,
            Order.created_at <= end_dt,
            Order.payment_status == "paid",
            Order.refund_status != "full",
        )
    )
    if category:
        query = query.filter(Product.category == category)
    rows = query.all()

    if rows:
        df = pd.DataFrame(
            [
                {
                    "product_id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "stock": p.stock,
                    "quantity": o.quantity,
                    "amount": o.amount,
                    "profit": (p.price - p.cost) * o.quantity,
                    "created_at": o.created_at,
                }
                for o, p in rows
            ]
        )
    else:
        df = pd.DataFrame(columns=["product_id", "name", "category", "stock", "quantity", "amount", "profit", "created_at"])

    top10 = (
        df.groupby(["product_id", "name"], as_index=False)["quantity"]
        .sum()
        .sort_values("quantity", ascending=False)
        .head(10)
        .to_dict(orient="records")
        if not df.empty
        else []
    )

    # 滞销定义：近15天销量 < 5
    recent_15 = df[df["created_at"] >= end_dt - timedelta(days=15)] if not df.empty else df
    slow = (
        recent_15.groupby(["product_id", "name", "stock"], as_index=False)["quantity"]
        .sum()
        .query("quantity < 5")
        .sort_values("quantity", ascending=True)
        .to_dict(orient="records")
        if not recent_15.empty
        else []
    )

    high_profit = (
        df.groupby(["product_id", "name"], as_index=False)["profit"]
        .sum()
        .sort_values("profit", ascending=False)
        .head(10)
        .to_dict(orient="records")
        if not df.empty
        else []
    )

    bad_reviews = (
        db.session.query(Review.tags)
        .filter(
            and_(
                Review.score <= 2,
                Review.created_at >= start_dt,
                Review.created_at <= end_dt,
            )
        )
        .all()
    )
    tag_count = {}
    for (tags,) in bad_reviews:
        if not tags:
            continue
        for tag in tags.split(","):
            key = tag.strip()
            if key:
                tag_count[key] = tag_count.get(key, 0) + 1
    bad_review_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)

    return {
        "top10_products": top10,
        "slow_moving_products": slow,
        "high_profit_products": high_profit,
        "bad_review_reason_ratio": [{"tag": k, "count": v} for k, v in bad_review_tags],
    }


def get_marketing_effectiveness(start_time=None, end_time=None, campaign_id=None):
    start_dt, end_dt = time_range_or_default(start_time, end_time, window_days=30)
    campaign_query = db.session.query(MarketingCampaign).filter(
        MarketingCampaign.start_time <= end_dt, MarketingCampaign.end_time >= start_dt
    )
    if campaign_id:
        campaign_query = campaign_query.filter(MarketingCampaign.id == int(campaign_id))
    campaigns = campaign_query.all()
    result = []
    for campaign in campaigns:
        order_stats = (
            db.session.query(func.count(Order.id), func.sum(Order.amount))
            .filter(
                Order.campaign_id == campaign.id,
                Order.created_at >= start_dt,
                Order.created_at <= end_dt,
                Order.payment_status == "paid",
                Order.refund_status != "full",
            )
            .first()
        )
        order_count = order_stats[0] or 0
        gmv = round(order_stats[1] or 0.0, 2)
        roi = round(safe_divide(gmv - campaign.cost, campaign.cost), 4) if campaign.cost else 0.0

        coupon_stats = (
            db.session.query(func.count(CouponUsage.id), func.sum(CouponUsage.used))
            .filter(
                CouponUsage.campaign_id == campaign.id,
                CouponUsage.created_at >= start_dt,
                CouponUsage.created_at <= end_dt,
            )
            .first()
        )
        coupon_receive = coupon_stats[0] or 0
        coupon_used = int(coupon_stats[1] or 0)
        coupon_usage_rate = round(safe_divide(coupon_used, coupon_receive) * 100, 2)

        ad_stats = (
            db.session.query(
                func.sum(AdPerformance.clicks),
                func.sum(AdPerformance.conversions),
                func.sum(AdPerformance.cost),
            )
            .filter(
                AdPerformance.campaign_id == campaign.id,
                AdPerformance.stat_date >= start_dt.date(),
                AdPerformance.stat_date <= end_dt.date(),
            )
            .first()
        )
        clicks = ad_stats[0] or 0
        conversions = ad_stats[1] or 0
        ad_cost = ad_stats[2] or 0.0

        result.append(
            {
                "campaign_id": campaign.id,
                "campaign_name": campaign.name,
                "campaign_type": campaign.campaign_type,
                "order_count": order_count,
                "gmv": gmv,
                "coupon_usage_rate": coupon_usage_rate,
                "clicks": clicks,
                "conversions": conversions,
                "ad_cost": round(ad_cost, 2),
                "roi": roi,
            }
        )

    low_efficiency = [r for r in result if r["roi"] < 0.1]
    return {"campaigns": result, "low_efficiency_campaigns": low_efficiency}


def get_decision_suggestions():
    _ensure_default_rules()
    segment_data = get_user_segments()
    product_data = get_product_diagnosis()
    marketing_data = get_marketing_effectiveness()

    rules = {
        r.rule_key: r
        for r in db.session.query(DecisionRule).filter(DecisionRule.enabled.is_(True)).all()
    }

    high_risk_users = [
        u for u in segment_data.get("segments", []) if u.get("segment") == "流失风险用户"
    ][:20]
    slow_products = product_data.get("slow_moving_products", [])[:10]
    hot_products = product_data.get("top10_products", [])[:10]
    low_eff_campaigns = marketing_data.get("low_efficiency_campaigns", [])[:10]

    user_rule = rules.get("high_churn_user_coupon")
    product_rule = rules.get("slow_product_bundle")
    marketing_rule = rules.get("low_roi_campaign_opt")

    user_suggestions = [
        {
            "user_id": item["user_id"],
            "suggestion": user_rule.action_text
            if user_rule
            else "发放专属满减券（满100减30）并结合短信触达。",
            "reason": (
                user_rule.reason_template.format(value=item["recency"])
                if user_rule
                else f"用户近{item['recency']}天未消费，存在流失风险。"
            ),
            "priority": _clamp_priority((user_rule.priority_weight if user_rule else 70) + int(item["recency"])),
        }
        for item in high_risk_users
    ]

    product_suggestions = []
    for idx, product in enumerate(slow_products):
        bundle = hot_products[idx % len(hot_products)]["name"] if hot_products else "店铺热销品"
        product_suggestions.append(
            {
                "product_id": product["product_id"],
                "product_name": product["name"],
                "suggestion": (
                    product_rule.action_text.replace("{bundle}", bundle)
                    if product_rule
                    else f"与 {bundle} 进行捆绑销售，设置组合优惠。"
                ),
                "reason": (
                    product_rule.reason_template.format(value=product["quantity"])
                    if product_rule
                    else f"近15天销量仅 {product['quantity']} 件，库存压力较高。"
                ),
                "priority": _clamp_priority(
                    (product_rule.priority_weight if product_rule else 65)
                    + max(0, 5 - int(product["quantity"])) * 5
                ),
            }
        )

    marketing_suggestions = []
    for c in low_eff_campaigns:
        marketing_suggestions.append(
            {
                "campaign_id": c["campaign_id"],
                "campaign_name": c["campaign_name"],
                "suggestion": marketing_rule.action_text
                if marketing_rule
                else "下调预算并重定向投放人群，A/B 测试新素材。",
                "reason": (
                    marketing_rule.reason_template.format(value=c["roi"])
                    if marketing_rule
                    else f"活动 ROI={c['roi']}，低于预期。"
                ),
                "priority": _clamp_priority(
                    (marketing_rule.priority_weight if marketing_rule else 60)
                    + int((0.1 - c["roi"]) * 100)
                ),
            }
        )

    return {
        "user_suggestions": user_suggestions,
        "product_suggestions": product_suggestions,
        "marketing_suggestions": marketing_suggestions,
    }


def _clamp_priority(value):
    return max(1, min(100, int(value)))


def _ensure_default_rules():
    defaults = [
        {
            "rule_key": "high_churn_user_coupon",
            "rule_name": "高流失风险用户券激活",
            "rule_type": "user",
            "threshold_value": 30,
            "action_text": "发放专属满减券（满100减30）并短信触达。",
            "reason_template": "用户最近消费距今 {value} 天，活跃度下降。",
            "priority_weight": 75,
        },
        {
            "rule_key": "slow_product_bundle",
            "rule_name": "滞销商品捆绑销售",
            "rule_type": "product",
            "threshold_value": 5,
            "action_text": "与 {bundle} 组合销售并设置组合折扣。",
            "reason_template": "近15天销量仅 {value} 件，存在滞销风险。",
            "priority_weight": 68,
        },
        {
            "rule_key": "low_roi_campaign_opt",
            "rule_name": "低ROI活动优化",
            "rule_type": "marketing",
            "threshold_value": 0.1,
            "action_text": "下调预算并优化投放人群，执行新素材 A/B 测试。",
            "reason_template": "活动 ROI={value}，建议及时优化。",
            "priority_weight": 62,
        },
    ]
    existing = {r.rule_key for r in db.session.query(DecisionRule.rule_key).all()}
    for item in defaults:
        if item["rule_key"] in existing:
            continue
        db.session.add(DecisionRule(**item))
    db.session.commit()


def get_decision_rules():
    _ensure_default_rules()
    rows = db.session.query(DecisionRule).order_by(DecisionRule.id.asc()).all()
    return [
        {
            "id": r.id,
            "rule_key": r.rule_key,
            "rule_name": r.rule_name,
            "rule_type": r.rule_type,
            "threshold_value": r.threshold_value,
            "action_text": r.action_text,
            "reason_template": r.reason_template,
            "priority_weight": r.priority_weight,
            "enabled": r.enabled,
        }
        for r in rows
    ]


def save_decision_rule(payload):
    rule_id = payload.get("id")
    if rule_id:
        rule = db.session.get(DecisionRule, int(rule_id))
        if not rule:
            raise ValueError("rule not found")
    else:
        rule = DecisionRule(rule_key=payload["rule_key"])
        db.session.add(rule)
    for field in [
        "rule_name",
        "rule_type",
        "threshold_value",
        "action_text",
        "reason_template",
        "priority_weight",
        "enabled",
    ]:
        if field in payload:
            setattr(rule, field, payload[field])
    db.session.commit()
    return {"id": rule.id}