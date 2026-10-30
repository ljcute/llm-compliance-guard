from fastapi.testclient import TestClient

from llm_compliance_guard.http_app import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_evaluate_and_rules():
    rules = client.get("/v1/rules")
    assert rules.status_code == 200
    body = rules.json()
    assert body["rule_set"] == "examples"
    assert len(body["rules"]) >= 4

    bad = client.post(
        "/v1/evaluate",
        json={"text": "稳赚不赔，保证到账", "trace_id": "http-1"},
    )
    assert bad.status_code == 200
    data = bad.json()
    assert data["allowed"] is False
    assert data["disposition"] == "block"
    assert data["audit"]["trace_id"] == "http-1"
