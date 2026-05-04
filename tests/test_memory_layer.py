from __future__ import annotations

from datetime import UTC, datetime, timedelta

from devcd.slices.memory_layer.models import MemoryScope
from devcd.slices.memory_layer.service import MemoryStore


def test_working_memory_expires_after_ttl() -> None:
    store = MemoryStore.with_ttl_seconds(1, episodic_seconds=10)
    entry = store.add_working({"type": "file_focus"})
    entry.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    assert store.list_by_scope(MemoryScope.WORKING) == []


def test_episodic_memory_expires_after_retention() -> None:
    store = MemoryStore.with_ttl_seconds(10, episodic_seconds=1)
    entry = store.add_episodic({"type": "branch_change"})
    entry.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    assert store.list_by_scope(MemoryScope.EPISODIC) == []


def test_semantic_memory_is_retained_without_expiry() -> None:
    store = MemoryStore.with_default_ttl()
    entry = store.add_semantic({"rule": "use metadata only"})

    assert entry.expires_at is None
    assert store.list_by_scope(MemoryScope.SEMANTIC)[0].content["rule"] == "use metadata only"