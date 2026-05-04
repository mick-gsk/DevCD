from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from devcd.slices.memory_layer.models import MemoryEntry, MemoryScope


class MemoryStore:
    def __init__(self, working_ttl: timedelta, episodic_ttl: timedelta) -> None:
        self._working_ttl = working_ttl
        self._episodic_ttl = episodic_ttl
        self._entries: list[MemoryEntry] = []

    @classmethod
    def with_default_ttl(cls) -> MemoryStore:
        return cls(working_ttl=timedelta(minutes=5), episodic_ttl=timedelta(days=7))

    @classmethod
    def with_ttl_seconds(cls, seconds: int, episodic_seconds: int = 604800) -> MemoryStore:
        return cls(
            working_ttl=timedelta(seconds=seconds),
            episodic_ttl=timedelta(seconds=episodic_seconds),
        )

    def add_working(
        self,
        content: dict[str, Any],
        *,
        source: str | None = None,
        policy_reason: str | None = None,
        timestamp: datetime | None = None,
    ) -> MemoryEntry:
        recorded_at = timestamp or datetime.now(UTC)
        entry = MemoryEntry(
            scope=MemoryScope.WORKING,
            timestamp=recorded_at,
            source=source,
            content=content,
            policy_reason=policy_reason,
            expires_at=recorded_at + self._working_ttl,
        )
        self._entries.append(entry)
        self._prune_expired_memory()
        return entry

    def add_episodic(
        self,
        content: dict[str, Any],
        *,
        source: str | None = None,
        policy_reason: str | None = None,
        timestamp: datetime | None = None,
    ) -> MemoryEntry:
        recorded_at = timestamp or datetime.now(UTC)
        entry = MemoryEntry(
            scope=MemoryScope.EPISODIC,
            timestamp=recorded_at,
            source=source,
            content=content,
            policy_reason=policy_reason,
            expires_at=recorded_at + self._episodic_ttl,
        )
        self._entries.append(entry)
        self._prune_expired_memory()
        return entry

    def add_semantic(
        self,
        content: dict[str, Any],
        *,
        source: str | None = None,
        policy_reason: str | None = None,
        timestamp: datetime | None = None,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            scope=MemoryScope.SEMANTIC,
            timestamp=timestamp or datetime.now(UTC),
            source=source,
            content=content,
            policy_reason=policy_reason,
            expires_at=None,
        )
        self._entries.append(entry)
        self._prune_expired_memory()
        return entry

    def list_by_scope(
        self,
        scope: MemoryScope,
        is_source_visible: Callable[[str | None], bool] | None = None,
    ) -> list[MemoryEntry]:
        self._prune_expired_memory()
        entries = [entry for entry in self._entries if entry.scope is scope]
        if is_source_visible is None:
            return entries
        return [entry for entry in entries if is_source_visible(entry.source)]

    def _prune_expired_memory(self) -> None:
        now = datetime.now(UTC)
        self._entries = [
            entry
            for entry in self._entries
            if entry.expires_at is None or entry.expires_at >= now
        ]
