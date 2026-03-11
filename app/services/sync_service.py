from datetime import datetime

from flask import current_app

from app.extensions import db
from app.models import DataSyncLog, Order, Product, User, UserBehavior
from app.utils.data_fetcher import DataFetcher
from app.utils.data_processor import (
    normalize_behaviors_dataframe,
    normalize_orders_dataframe,
    normalize_products_dataframe,
    normalize_users_dataframe,
)


def _upsert_users(users_df):
    inserted = 0
    user_map = {u.username: u.id for u in db.session.query(User).all()}
    for row in users_df.to_dict(orient="records"):
        if row["username"] in user_map:
            continue
        user = User(
            username=row["username"],
            age=row["age"],
            gender=row["gender"],
            region=row["region"],
        )
        db.session.add(user)
        inserted += 1
    db.session.flush()
    user_map = {u.username: u.id for u in db.session.query(User).all()}
    return inserted, user_map


def _upsert_products(products_df):
    inserted = 0
    product_map = {p.name: p.id for p in db.session.query(Product).all()}
    for row in products_df.to_dict(orient="records"):
        if row["name"] in product_map:
            continue
        product = Product(
            name=row["name"],
            category=row["category"],
            price=row["price"],
            cost=row["cost"],
            stock=row["stock"],
            rating=row["rating"],
        )
        db.session.add(product)
        inserted += 1
    db.session.flush()
    product_map = {p.name: p.id for p in db.session.query(Product).all()}
    return inserted, product_map


def _insert_orders(orders_df, user_map, product_map):
    inserted = 0
    existing_order_no = {x[0] for x in db.session.query(Order.order_no).all()}
    for row in orders_df.to_dict(orient="records"):
        if row["order_no"] in existing_order_no:
            continue
        user_id = user_map.get(row["username"])
        product_id = product_map.get(row["product_name"])
        if not user_id or not product_id:
            continue
        order = Order(
            order_no=row["order_no"],
            user_id=user_id,
            product_id=product_id,
            quantity=int(row["quantity"]),
            amount=float(row["amount"]),
            payment_status=row["payment_status"],
            refund_status=row["refund_status"],
            created_at=row["created_at"],
        )
        db.session.add(order)
        inserted += 1
    return inserted


def _insert_behaviors(behaviors_df, user_map, product_map):
    inserted = 0
    for row in behaviors_df.to_dict(orient="records"):
        user_id = user_map.get(row["username"])
        product_id = product_map.get(row["product_name"])
        if not user_id or not product_id:
            continue
        behavior = UserBehavior(
            user_id=user_id,
            product_id=product_id,
            behavior_type=row["behavior_type"],
            created_at=row["created_at"],
        )
        db.session.add(behavior)
        inserted += 1
    return inserted


def run_data_sync(source="mock_api", mode="manual", taobao_endpoint=None, mysql_uri=None):
    taobao_endpoint = taobao_endpoint or current_app.config.get("TAOBAO_API_ENDPOINT")
    mysql_uri = mysql_uri or current_app.config.get("EXTERNAL_MYSQL_URI")
    started_at = datetime.utcnow()
    log = DataSyncLog(source=source, mode=mode, status="running", started_at=started_at)
    db.session.add(log)
    db.session.commit()

    try:
        fetched = DataFetcher().fetch(
            source=source, taobao_endpoint=taobao_endpoint, mysql_uri=mysql_uri
        )
        users_df = normalize_users_dataframe(fetched["users"])
        products_df = normalize_products_dataframe(fetched["products"])
        orders_df = normalize_orders_dataframe(fetched["orders"])
        behaviors_df = normalize_behaviors_dataframe(fetched["behaviors"])

        user_inserted, user_map = _upsert_users(users_df)
        product_inserted, product_map = _upsert_products(products_df)
        order_inserted = _insert_orders(orders_df, user_map, product_map)
        behavior_inserted = _insert_behaviors(behaviors_df, user_map, product_map)
        db.session.commit()

        log.status = "success"
        log.inserted_users = user_inserted
        log.inserted_products = product_inserted
        log.inserted_orders = order_inserted
        log.inserted_behaviors = behavior_inserted
        log.finished_at = datetime.utcnow()
        log.message = "sync completed"
        db.session.commit()

        return {
            "log_id": log.id,
            "source": source,
            "mode": mode,
            "status": "success",
            "inserted_users": user_inserted,
            "inserted_products": product_inserted,
            "inserted_orders": order_inserted,
            "inserted_behaviors": behavior_inserted,
        }
    except Exception as exc:
        db.session.rollback()
        log.status = "failed"
        log.finished_at = datetime.utcnow()
        log.message = str(exc)[:250]
        db.session.add(log)
        db.session.commit()
        return {"log_id": log.id, "source": source, "mode": mode, "status": "failed", "error": str(exc)}


def get_sync_logs(limit=20):
    rows = (
        db.session.query(DataSyncLog)
        .order_by(DataSyncLog.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "source": r.source,
            "mode": r.mode,
            "status": r.status,
            "inserted_users": r.inserted_users,
            "inserted_products": r.inserted_products,
            "inserted_orders": r.inserted_orders,
            "inserted_behaviors": r.inserted_behaviors,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "message": r.message,
        }
        for r in rows
    ]
