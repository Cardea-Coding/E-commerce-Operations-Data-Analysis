import time


def _latency_ms(client, path):
    t0 = time.perf_counter()
    resp = client.get(path)
    elapsed = (time.perf_counter() - t0) * 1000
    return resp, elapsed


def test_dashboard_overview_under_2s(client):
    # 首次请求包含连接与缓存预热，使用第二次请求评估业务响应时间
    _latency_ms(client, "/api/dashboard/overview")
    resp, latency = _latency_ms(client, "/api/dashboard/overview")
    assert resp.status_code == 200
    assert latency < 2000


def test_report_interfaces_available(client):
    metric_tpl = client.post(
        "/api/reports/metric-templates",
        json={
            "name": "phase5_metric_sample",
            "expression": "a/b",
            "variables_schema": ["a", "b"],
        },
    )
    assert metric_tpl.status_code == 200

    report_tpl = client.post(
        "/api/reports/report-templates",
        json={
            "name": "phase5_report_sample",
            "query_type": "dashboard",
            "filters": {},
            "columns": ["gmv", "order_count"],
        },
    )
    assert report_tpl.status_code == 200
