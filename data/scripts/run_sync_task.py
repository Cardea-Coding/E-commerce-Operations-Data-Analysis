import argparse
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app
from app.services.sync_service import run_data_sync


def main():
    parser = argparse.ArgumentParser(description="数据同步任务执行器")
    parser.add_argument("--source", default="mock_api", choices=["mock_api", "taobao_api", "mysql"])
    parser.add_argument("--interval", type=int, default=30, help="循环模式下的间隔分钟")
    parser.add_argument("--loop", action="store_true", help="是否循环执行")
    parser.add_argument("--taobao-endpoint", default=None)
    parser.add_argument("--mysql-uri", default=None)
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        if not args.loop:
            result = run_data_sync(
                source=args.source,
                mode="manual",
                taobao_endpoint=args.taobao_endpoint,
                mysql_uri=args.mysql_uri,
            )
            print(result)
            return

        while True:
            result = run_data_sync(
                source=args.source,
                mode="schedule",
                taobao_endpoint=args.taobao_endpoint,
                mysql_uri=args.mysql_uri,
            )
            print(result)
            time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
