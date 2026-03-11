import random
from datetime import datetime, timedelta

import pandas as pd
import requests
from sqlalchemy import create_engine


class MockApiSource:
    def fetch(self):
        now = datetime.utcnow()
        users = [
            {
                "username": f"sync_user_{i}",
                "age": random.randint(18, 45),
                "gender": random.choice(["male", "female"]),
                "region": random.choice(["华东", "华南", "华北"]),
            }
            for i in range(1, 11)
        ]
        products = [
            {
                "name": f"同步商品{i}",
                "category": random.choice(["服装", "家居", "美妆"]),
                "price": round(random.uniform(50, 500), 2),
                "cost": round(random.uniform(20, 200), 2),
                "stock": random.choice([None, random.randint(10, 200)]),
                "rating": round(random.uniform(3.5, 5.0), 1),
            }
            for i in range(1, 9)
        ]
        orders = []
        behaviors = []
        for i in range(1, 31):
            user = random.choice(users)
            product = random.choice(products)
            orders.append(
                {
                    "order_no": f"SYNC{now.strftime('%Y%m%d%H%M')}{i:04d}",
                    "username": user["username"],
                    "product_name": product["name"],
                    "quantity": random.randint(1, 3),
                    "amount": round(product["price"] * random.uniform(0.8, 1.0), 2),
                    "payment_status": random.choice(["paid", "paid", "pending"]),
                    "refund_status": random.choice(["none", "none", "partial"]),
                    "created_at": now - timedelta(minutes=random.randint(1, 120)),
                }
            )
            behaviors.append(
                {
                    "username": user["username"],
                    "product_name": product["name"],
                    "behavior_type": random.choice(["view", "add_to_cart", "favorite"]),
                    "created_at": now - timedelta(minutes=random.randint(1, 180)),
                }
            )
        return {
            "users": pd.DataFrame(users),
            "products": pd.DataFrame(products),
            "orders": pd.DataFrame(orders),
            "behaviors": pd.DataFrame(behaviors),
        }


class TaobaoApiSource:
    def __init__(self, endpoint=None, timeout=5):
        self.endpoint = endpoint
        self.timeout = timeout

    def fetch(self):
        if not self.endpoint:
            return MockApiSource().fetch()
        # 示例：真实接入时根据淘宝开放平台签名规范改造
        resp = requests.get(self.endpoint, timeout=self.timeout)
        resp.raise_for_status()
        payload = resp.json()
        return {
            "users": pd.DataFrame(payload.get("users", [])),
            "products": pd.DataFrame(payload.get("products", [])),
            "orders": pd.DataFrame(payload.get("orders", [])),
            "behaviors": pd.DataFrame(payload.get("behaviors", [])),
        }


class MySQLSource:
    def __init__(self, uri):
        self.uri = uri

    def fetch(self):
        if not self.uri:
            return MockApiSource().fetch()
        engine = create_engine(self.uri)
        users = pd.read_sql("SELECT username, age, gender, region FROM users LIMIT 500", engine)
        products = pd.read_sql(
            "SELECT name, category, price, cost, stock, rating FROM products LIMIT 500", engine
        )
        orders = pd.read_sql(
            """
            SELECT order_no, username, product_name, quantity, amount, payment_status, refund_status, created_at
            FROM v_orders_for_sync
            ORDER BY created_at DESC
            LIMIT 2000
            """,
            engine,
        )
        behaviors = pd.read_sql(
            """
            SELECT username, product_name, behavior_type, created_at
            FROM v_behaviors_for_sync
            ORDER BY created_at DESC
            LIMIT 5000
            """,
            engine,
        )
        return {
            "users": users,
            "products": products,
            "orders": orders,
            "behaviors": behaviors,
        }


class DataFetcher:
    """多源接入统一入口。"""

    def fetch(self, source="mock_api", taobao_endpoint=None, mysql_uri=None):
        source = (source or "mock_api").lower()
        if source == "taobao_api":
            data = TaobaoApiSource(endpoint=taobao_endpoint).fetch()
        elif source == "mysql":
            data = MySQLSource(mysql_uri).fetch()
        else:
            data = MockApiSource().fetch()
        return {
            "source": source,
            "fetched_at": datetime.utcnow().isoformat(),
            **data,
        }