import pandas as pd


def normalize_users_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["username", "age", "gender", "region"])
    data = df.copy()
    data = data.rename(columns={"name": "username"})
    required = ["username", "age", "gender", "region"]
    for col in required:
        if col not in data.columns:
            data[col] = None
    data = data[required]
    data["username"] = data["username"].fillna("").astype(str).str.strip()
    data = data[data["username"] != ""]
    data["age"] = data["age"].fillna(25).astype(int).clip(lower=10, upper=90)
    data["gender"] = data["gender"].fillna("unknown")
    data["region"] = data["region"].fillna("未知")
    return data.drop_duplicates(subset=["username"])


def normalize_products_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["name", "category", "price", "cost", "stock", "rating"])
    data = df.copy()
    required = ["name", "category", "price", "cost", "stock", "rating"]
    for col in required:
        if col not in data.columns:
            data[col] = None
    data = data[required]
    data["name"] = data["name"].fillna("").astype(str).str.strip()
    data = data[data["name"] != ""]
    data["category"] = data["category"].fillna("未分类")
    data["price"] = data["price"].fillna(0).astype(float).clip(lower=0)
    data["cost"] = data["cost"].fillna(0).astype(float).clip(lower=0)
    data["rating"] = data["rating"].fillna(5).astype(float).clip(lower=1, upper=5)
    data = fill_product_stock_missing(data)
    return data.drop_duplicates(subset=["name"])


def normalize_orders_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "order_no",
                "username",
                "product_name",
                "quantity",
                "amount",
                "payment_status",
                "refund_status",
                "created_at",
            ]
        )
    data = df.copy()
    required = [
        "order_no",
        "username",
        "product_name",
        "quantity",
        "amount",
        "payment_status",
        "refund_status",
        "created_at",
    ]
    for col in required:
        if col not in data.columns:
            data[col] = None
    data = data[required]
    data["order_no"] = data["order_no"].fillna("").astype(str).str.strip()
    data["username"] = data["username"].fillna("").astype(str).str.strip()
    data["product_name"] = data["product_name"].fillna("").astype(str).str.strip()
    data = data[(data["order_no"] != "") & (data["username"] != "") & (data["product_name"] != "")]
    data["created_at"] = pd.to_datetime(data["created_at"], errors="coerce")
    data = data.dropna(subset=["created_at"])
    data["payment_status"] = data["payment_status"].fillna("paid")
    data["refund_status"] = data["refund_status"].fillna("none")
    data = clean_orders_dataframe(data)
    return data.drop_duplicates(subset=["order_no"])


def normalize_behaviors_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["username", "product_name", "behavior_type", "created_at"])
    data = df.copy()
    required = ["username", "product_name", "behavior_type", "created_at"]
    for col in required:
        if col not in data.columns:
            data[col] = None
    data = data[required]
    data["username"] = data["username"].fillna("").astype(str).str.strip()
    data["product_name"] = data["product_name"].fillna("").astype(str).str.strip()
    data["behavior_type"] = data["behavior_type"].fillna("view")
    data["created_at"] = pd.to_datetime(data["created_at"], errors="coerce")
    data = data.dropna(subset=["created_at"])
    data = data[(data["username"] != "") & (data["product_name"] != "")]
    # 为复用既有异常点击清洗，构造临时 user_id/product_id 键
    data["user_id"] = data["username"]
    data["product_id"] = data["product_name"]
    data = clean_behavior_dataframe(data)
    return data.drop(columns=["user_id", "product_id"])


def clean_orders_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    data = df.copy()
    # 剔除订单金额极端值（普通场景中 >10万视为异常）
    data = data[data["amount"] <= 100000]
    data = data[data["amount"] >= 0]

    # 数量和金额兜底
    data["quantity"] = data["quantity"].fillna(1).clip(lower=1)
    data["amount"] = data["amount"].fillna(0.0).clip(lower=0.0)
    return data


def clean_behavior_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    data = df.copy()
    data["created_at"] = pd.to_datetime(data["created_at"])
    data["minute_bucket"] = data["created_at"].dt.floor("min")
    click_only = data[data["behavior_type"] == "view"]
    abnormal = (
        click_only.groupby(["user_id", "product_id", "minute_bucket"])
        .size()
        .reset_index(name="cnt")
    )
    abnormal = abnormal[abnormal["cnt"] > 50]
    if abnormal.empty:
        return data.drop(columns=["minute_bucket"])

    data = data.merge(
        abnormal[["user_id", "product_id", "minute_bucket"]],
        on=["user_id", "product_id", "minute_bucket"],
        how="left",
        indicator=True,
    )
    data = data[data["_merge"] == "left_only"]
    return data.drop(columns=["minute_bucket", "_merge"])


def fill_product_stock_missing(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "stock" not in df.columns or "category" not in df.columns:
        return df
    data = df.copy()
    category_mean = data.groupby("category")["stock"].transform("mean")
    data["stock"] = data["stock"].fillna(category_mean).fillna(0).astype(int)
    return data