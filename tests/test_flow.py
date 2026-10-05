from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.pipeline import analyze, validate_selection


def client(tmp_path: Path, demo=True):
    settings = Settings(tmp_path, demo, "test-secret", "", "", "")
    return TestClient(create_app(settings))


def test_demo_end_to_end_and_idempotency(tmp_path):
    c = client(tmp_path)
    first = c.post("/api/demo/run/pricing")
    assert first.status_code == 200
    record = first.json()["record"]
    assert record["status"] == "complete"
    assert record["category"] == "报价咨询"
    assert record["analysis_mode"] == "规则演示"
    assert record["notification"]["sent"] is False
    assert record["notification"]["channel"] == "simulation"
    assert "未发送" in record["draft"]
    assert all(item["evidence"] in record["body"] for item in record["requirements"])
    assert [x["stage"] for x in record["events"]] == ["received", "classified", "extracted", "drafted", "notified"]
    second = c.post("/api/demo/run/pricing").json()
    assert second["duplicate"] is True
    assert second["id"] == first.json()["id"]
    assert len(c.get("/api/emails").json()) == 1
    assert c.get("/api/status").json()["email_count"] == 1
    c2 = client(tmp_path)
    assert c2.get("/api/emails/1").json()["notification"]["sent"] is False


def test_public_restrictions_and_webhook_auth(tmp_path):
    c = client(tmp_path)
    payload = {"message_id": "test-123", "from_name": "测试", "from_email": "test@example.com", "subject": "咨询", "body": "你好，我想了解报价，请回复。"}
    assert c.post("/api/webhook/email", json=payload, headers={"X-Webhook-Token": "test-secret"}).status_code == 403
    assert c.post("/api/demo/run/unknown").status_code == 404
    local = client(tmp_path / "local", demo=False)
    assert local.post("/api/webhook/email", json=payload).status_code == 401
    assert local.post("/api/webhook/email", json=payload, headers={"X-Webhook-Token": "wrong"}).status_code == 401
    assert local.post("/api/webhook/email", json=payload, headers={"X-Webhook-Token": "test-secret"}).status_code == 200
    altered = dict(payload, body="你好，我想了解其他问题，请回复。")
    assert local.post("/api/webhook/email", json=altered, headers={"X-Webhook-Token": "test-secret"}).status_code == 409


def test_all_fictional_scenarios(tmp_path):
    c = client(tmp_path)
    expected = {"pricing": "报价咨询", "support": "技术支持", "partnership": "商务合作", "general": "一般咨询"}
    for sample, category in expected.items():
        record = c.post("/api/demo/run/" + sample).json()["record"]
        assert record["category"] == category
        assert record["requirements"]
        assert len(record["events"]) == 5
    assert c.get("/api/status").json()["email_count"] == 4


def test_model_selection_maps_to_original_and_rejects_bad_ids(monkeypatch, tmp_path):
    from app.samples import SAMPLES
    class Response:
        def raise_for_status(self):
            pass
        def json(self):
            return {"choices": [{"message": {"content": '{"category":"报价咨询","requirement_ids":[1,2]}'}}]}
    monkeypatch.setattr("app.pipeline.httpx.post", lambda *args, **kwargs: Response())
    settings = Settings(tmp_path, True, "", "http://model/v1", "", "test-model")
    result, draft, mode, fallback = analyze(SAMPLES[0], settings)
    assert mode == "LLM 分类/提取"
    assert fallback is None
    assert all(item["evidence"] in SAMPLES[0]["body"] for item in result["requirements"])
    assert result["urgency"] == "中"
    assert "未发送" in draft
    try:
        validate_selection({"category": "报价咨询", "urgency": "低", "requirement_ids": [99]}, ["请介绍团队版报价"])
    except ValueError as exc:
        assert "句子" in str(exc)
    else:
        raise AssertionError("不存在的原文编号应被拒绝")


def test_model_category_normalization_and_unsupported_claim(monkeypatch, tmp_path):
    from app.samples import SAMPLES
    class Response:
        def __init__(self, category):
            self.category = category
        def raise_for_status(self):
            pass
        def json(self):
            return {"choices": [{"message": {"content": '{"category":"' + self.category + '","requirement_ids":[1,2]}'}}]}
    settings = Settings(tmp_path, True, "", "http://model/v1", "", "test-model")
    monkeypatch.setattr("app.pipeline.httpx.post", lambda *args, **kwargs: Response("产品试用/报价咨询"))
    result, _, mode, fallback = analyze(SAMPLES[0], settings)
    assert (result["category"], mode, fallback) == ("报价咨询", "LLM 提取 + 类别规范化", None)
    monkeypatch.setattr("app.pipeline.httpx.post", lambda *args, **kwargs: Response("产品试用"))
    result, _, mode, fallback = analyze(SAMPLES[3], settings)
    assert (result["category"], mode, fallback) == ("一般咨询", "规则回退", "ValueError")
