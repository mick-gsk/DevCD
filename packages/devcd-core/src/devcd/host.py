from __future__ import annotations

from fastapi import FastAPI

from devcd.kernel.settings import DevCDSettings
from devcd.slices.events.ledger import EventLedger
from devcd.slices.host_state_engine.api import router as state_router
from devcd.slices.host_state_engine.service import StateEngine
from devcd.slices.memory_layer.service import MemoryStore
from devcd.slices.policy_layer.service import PolicyEngine


def create_app(settings: DevCDSettings | None = None) -> FastAPI:
    resolved_settings = settings or DevCDSettings.load()
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
    app.state.state_engine = state_engine
    app.include_router(state_router)
    return app
