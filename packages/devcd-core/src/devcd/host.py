from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from devcd.kernel.settings import DevCDSettings
from devcd.slices.ambient_context.api import router as ambient_context_router
from devcd.slices.ambient_context.service import AmbientContextService
from devcd.slices.events.ledger import EventLedger
from devcd.slices.host_state_engine.api import router as state_router
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.models import PolicyDecision, PolicyDecisionKind
from devcd.slices.policy_layer.service import PolicyEngine

_LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}


def _ensure_api_token(settings: DevCDSettings) -> str:
    if settings.api_token:
        return settings.api_token

    token = str(uuid4())
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    token_path = settings.runtime_dir / "token"
    token_path.write_text(token, encoding="utf-8")
    token_path.chmod(0o600)
    settings.api_token = token
    return token


def create_app(settings: DevCDSettings | None = None) -> FastAPI:
    resolved_settings = settings or DevCDSettings.load()
    api_token = _ensure_api_token(resolved_settings)
    policy_engine = PolicyEngine.from_settings(resolved_settings)
    memory_store = MemoryStore.with_ttl_seconds(resolved_settings.working_memory_ttl_seconds)
    event_ledger = EventLedger(resolved_settings.ledger_path)
    state_engine = StateEngine(
        policy_engine=policy_engine,
        memory_store=memory_store,
        event_ledger=event_ledger,
    )

    app = FastAPI(title="DevCD", version="0.1.0")
    app.state.settings = resolved_settings
    app.state.api_token = api_token
    app.state.state_engine = state_engine
    app.state.ambient_context_service = AmbientContextService(
        state_engine=state_engine,
        memory_store=memory_store,
        policy_engine=policy_engine,
    )
    state_engine.rebuild_from_ledger()

    @app.middleware("http")
    async def require_loopback_and_token(request, call_next):  # type: ignore[no-untyped-def]
        if request.url.path == "/openapi.json":
            return await call_next(request)

        if request.url.hostname not in _LOOPBACK_HOSTS:
            decision = PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="non-loopback access is denied by the MVP local policy",
                operation="auth",
            )
            return JSONResponse(status_code=401, content=decision.model_dump(mode="json"))

        expected_header = f"Bearer {request.app.state.api_token}"
        authorization = request.headers.get("Authorization")
        if authorization != expected_header:
            decision = PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="missing or invalid local bearer token",
                operation="auth",
            )
            return JSONResponse(status_code=401, content=decision.model_dump(mode="json"))

        return await call_next(request)

    app.include_router(state_router)
    app.include_router(ambient_context_router)
    return app
