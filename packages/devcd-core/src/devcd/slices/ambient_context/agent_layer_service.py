from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from devcd.slices.ambient_context.service import AmbientContextService

logger = logging.getLogger(__name__)


class AgentLayerService:
    """Service that manages the agent layer for ambient context."""

    def __init__(self, ambient_context_service: AmbientContextService) -> None:
        self._ambient_context_service = ambient_context_service
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Start the agent layer service."""
        if self._running:
            logger.warning("AgentLayerService already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("AgentLayerService started")

    async def stop(self) -> None:
        """Stop the agent layer service."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("AgentLayerService stopped")

    async def _run(self) -> None:
        """Main loop for the agent layer service."""
        while self._running:
            try:
                await self._process_pending_events()
                await asyncio.sleep(0.1)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error in AgentLayerService loop")
                await asyncio.sleep(1.0)

    async def _process_pending_events(self) -> None:
        """Process pending events from the ambient context."""
        events = await self._ambient_context_service.get_pending_agent_events()
        for event in events:
            await self._handle_event(event)

    async def _handle_event(self, event: dict[str, Any]) -> None:
        """Handle a single event."""
        event_type = event.get("type", "unknown")
        logger.debug("Handling event: %s", event_type)
        await self._ambient_context_service.mark_event_processed(event.get("id", ""))
