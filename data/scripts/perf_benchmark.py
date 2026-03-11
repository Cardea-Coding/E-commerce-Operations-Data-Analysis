import argparse
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import create_app


def benchmark_endpoint(path, total_requests=100, concurrency=10):
    app = create_app()

    def run_one():
        t0 = time.perf_counter()
        with app.test_client() as c:
            resp = c.get(path)
            elapsed = (time.perf_counter() - t0) * 1000
            return resp.status_code, elapsed

    latencies = []
    status_count = {}
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(run_one) for _ in range(total_requests)]
        for f in as_completed(futures):
            status, latency = f.result()
            latencies.append(latency)
            status_count[status] = status_count.get(status, 0) + 1
    total_elapsed = time.perf_counter() - t_start

    latencies.sort()
    p95_idx = int(len(latencies) * 0.95) - 1
    p95_idx = max(0, min(p95_idx, len(latencies) - 1))
    report = {
        "endpoint": path,
        "total_requests": total_requests,
        "concurrency": concurrency,
        "status_count": status_count,
        "avg_ms": round(statistics.mean(latencies), 2),
        "p95_ms": round(latencies[p95_idx], 2),
        "max_ms": round(max(latencies), 2),
        "throughput_rps": round(total_requests / total_elapsed, 2),
    }
    return report


def main():
    parser = argparse.ArgumentParser(description="性能压测脚本（第五阶段）")
    parser.add_argument("--requests", type=int, default=120)
    parser.add_argument("--concurrency", type=int, default=12)
    args = parser.parse_args()

    endpoints = [
        "/api/dashboard/overview",
        "/api/dashboard/trend?granularity=day",
        "/api/users/segments",
        "/api/products/diagnosis",
        "/api/marketing/effectiveness",
    ]
    for ep in endpoints:
        print(benchmark_endpoint(ep, total_requests=args.requests, concurrency=args.concurrency))


if __name__ == "__main__":
    main()
