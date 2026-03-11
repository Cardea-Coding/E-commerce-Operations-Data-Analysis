def test_core_endpoints_ok(client):
    endpoints = [
        "/health",
        "/",
        "/api/dashboard/overview",
        "/api/dashboard/trend?granularity=day",
        "/api/users/segments",
        "/api/products/diagnosis",
        "/api/marketing/effectiveness",
        "/api/decision/suggestions",
        "/api/system/perf-summary",
    ]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200, ep


def test_sync_and_rules_endpoints(client):
    resp = client.get("/api/decision/rules")
    assert resp.status_code == 200
    rules = resp.get_json()["data"]
    assert isinstance(rules, list)
    assert len(rules) >= 1

    sync_resp = client.post("/api/data-sync/run", json={"source": "mock_api", "mode": "manual"})
    assert sync_resp.status_code == 200
    assert sync_resp.get_json()["data"]["status"] in {"success", "failed"}
