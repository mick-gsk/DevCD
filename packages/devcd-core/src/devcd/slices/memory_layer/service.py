from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from devcd.slices.memory_layer.models import MemoryEntry, MemoryScope


class MemoryStore:
    def __init__(self, working_ttl: timedelta) -> None:
        self._working_ttl = working_ttl
        self._entries: list[MemoryEntry] = []

    @classmethod
    def with_default_ttl(cls) -> MemoryStore:
        return cls(working_ttl=timedelta(minutes=5))

    @classmethod
    def with_ttl_seconds(cls, seconds: int) -> MemoryStore:
        return cls(working_ttl=timedelta(seconds=seconds))

    def add_working(self, content: dict[str, Any]) -> MemoryEntry:
        entry = MemoryEntry(scope=MemoryScope.WORKING, content=content)
        self._entries.append(entry)
        self._prune_expired_working_memory()
        return entry

    def list_by_scope(self, scope: MemoryScope) -> list[MemoryEntry]:
        self._prune_expired_working_memory()
        return [entry for entry in self._entries if entry.scope is scope]

    def _prune_expired_working_memory(self) -> None:
        cutoff = datetime.now(UTC) - self._working_ttl
        self._entries = [
            entry
            for entry in self._entries
            if entry.scope is not MemoryScope.WORKING or entry.timestamp >= cutoff
        ]
