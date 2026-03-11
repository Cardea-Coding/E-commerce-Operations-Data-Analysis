import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "graduation-project-dev-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@127.0.0.1:3306/ecommerce_analysis?charset=utf8mb4",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis 配置
    REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

    # 默认查询窗口（天）
    DEFAULT_WINDOW_DAYS = int(os.getenv("DEFAULT_WINDOW_DAYS", "30"))

    # 数据接入配置（第二阶段）
    TAOBAO_API_ENDPOINT = os.getenv("TAOBAO_API_ENDPOINT", "")
    EXTERNAL_MYSQL_URI = os.getenv("EXTERNAL_MYSQL_URI", "")
