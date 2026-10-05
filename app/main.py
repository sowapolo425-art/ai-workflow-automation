from collections import defaultdict, deque
from pathlib import Path
from time import monotonic
import secrets

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, EmailStr

from .config import Settings
from .pipeline import analyze
from .samples import SAMPLE_BY_ID, SAMPLES
from .store import Store


class IncomingEmail(BaseModel):
    message_id: str = Field(min_length=3, max_length=160)
    from_name: str = Field(min_length=1, max_length=120)
    from_email: EmailStr
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=10, max_length=6000)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    store = Store(settings.data_dir)
    app = FastAPI(title="AI 工作流自动化 B", version="1.0.0")
    app.state.store = store
    hits: dict[str, deque] = defaultdict(deque)

    def limited(request: Request):
        ip = request.client.host if request.client else "unknown"
        now = monotonic()
        recent = hits[ip]
        while recent and now - recent[0] > 60:
            recent.popleft()
        if len(recent) >= 12:
            raise HTTPException(429, "演示操作过于频繁，请一分钟后重试")
        recent.append(now)

    def process(email: dict):
        try:
            email_id, duplicate = store.claim(email)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if duplicate:
            return {"id": email_id, "duplicate": True, "record": store.get(email_id)}
        try:
            analysis, draft, mode, fallback = analyze(email, settings)
            if fallback:
                store.add_event(email_id, "fallback", f"模型结果未通过校验或不可用：{fallback}；改用规则演示")
            store.finish(email_id, analysis, draft, mode)
        except Exception as exc:
            store.fail(email_id, type(exc).__name__)
            raise HTTPException(500, "处理失败；请查看审计记录") from exc
        return {"id": email_id, "duplicate": False, "record": store.get(email_id)}

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @app.get("/api/status")
    def status():
        return {"ok": True, "demo_mode": settings.demo_mode, "analysis_mode": "LLM 可用，失败回退规则" if settings.llm_enabled else "规则演示", "email_count": store.count(), "outbound_email": False, "outbound_notifications": False}

    @app.get("/api/samples")
    def samples():
        return SAMPLES

    @app.post("/api/demo/run/{sample_id}")
    def run_demo(sample_id: str, request: Request):
        if sample_id not in SAMPLE_BY_ID:
            raise HTTPException(404, "没有此演示样本")
        limited(request)
        return process(SAMPLE_BY_ID[sample_id])

    @app.post("/api/webhook/email")
    def webhook(email: IncomingEmail, x_webhook_token: str | None = Header(default=None)):
        if settings.demo_mode:
            raise HTTPException(403, "公网演示仅允许预置的虚构样本")
        if not settings.webhook_token or not x_webhook_token or not secrets.compare_digest(x_webhook_token, settings.webhook_token):
            raise HTTPException(401, "Webhook 令牌无效")
        return process(email.model_dump())

    @app.get("/api/emails")
    def emails():
        return store.list()

    @app.get("/api/emails/{email_id}")
    def email_detail(email_id: int):
        record = store.get(email_id)
        if not record:
            raise HTTPException(404, "记录不存在")
        return record

    return app


app = create_app()
