from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from devcd.slices.events.models import DevEvent
from devcd.slices.policy_layer.models import PolicyDecision


class EventLedger:
    def __init__(self, path: Path | None) -> None:
        self._path = path

    @classmethod
    def local_default(cls) -> EventLedger:
        return cls(Path(".devcd/events.jsonl"))

    @classmethod
    def disabled(cls) -> EventLedger:
        return cls(None)

    def append(self, event: DevEvent, decision: PolicyDecision) -> None:
        if self._path is None:
            return
        self._path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "event": event.model_dump(mode="json"),
            "policy_decision": decision.model_dump(mode="json"),
        }
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")

    def read_records(self) -> list[tuple[DevEvent, PolicyDecision]]:
        if self._path is None or not self._path.exists():
            return []

        records: list[tuple[DevEvent, PolicyDecision]] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                raw_record: dict[str, Any] = json.loads(line)
            except json.JSONDecodeError:
                continue
            raw_policy_decision = dict(raw_record["policy_decision"])
            raw_policy_decision.setdefault("operation", "store")
            records.append(
                (
                    DevEvent.model_validate(raw_record["event"]),
                    PolicyDecision.model_validate(raw_policy_decision),
                )
            )
        return records
