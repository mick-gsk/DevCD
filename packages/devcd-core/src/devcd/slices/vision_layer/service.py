from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSource
from devcd.slices.policy_layer.service import PolicyEngine
from devcd.slices.vision_layer.models import (
    NorthStarVersion,
    VisionAlignmentSignal,
    VisionBlock,
    VisionRecord,
)

_SENSITIVE_PATTERNS = [
    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}"),  # long base64-like token
    re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),  # email address
    re.compile(r"[a-zA-Z][a-zA-Z0-9+\-.]*://[^:]+:[^@]+@"),  # URL with credentials
]

_HISTORY_MAX = 100
_ALIGNMENT_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
_ALIGNMENT_STOP_WORDS = {
    "about",
    "agent",
    "agents",
    "build",
    "check",
    "current",
    "into",
    "keep",
    "next",
    "run",
    "surface",
    "that",
    "their",
    "this",
    "with",
}


class VisionService:
    def __init__(
        self,
        runtime_dir: Path,
        event_ledger: EventLedger | None = None,
    ) -> None:
        self._runtime_dir = runtime_dir
        self._vision_path = runtime_dir / "vision.json"
        self._event_ledger = event_ledger

    def load(self) -> VisionRecord | None:
        if not self._vision_path.exists():
            return None
        try:
            return VisionRecord.model_validate_json(self._vision_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"vision record at {self._vision_path} is corrupted: {exc}") from exc

    def save(self, record: VisionRecord) -> None:
        self._runtime_dir.mkdir(parents=True, exist_ok=True)
        tmp = self._vision_path.with_suffix(".json.tmp")
        tmp.write_text(record.model_dump_json(indent=2), encoding="utf-8")
        tmp.replace(self._vision_path)

    def init_vision(
        self,
        domain: str,
        north_star: str,
        rationale: str | None = None,
        guided: bool = False,
    ) -> VisionRecord:
        now = datetime.now(UTC)
        record = VisionRecord(
            domain=domain,
            north_star=north_star,
            rationale=rationale,
            created_at=now,
            updated_at=now,
            guided=guided,
        )
        self.save(record)
        if self._event_ledger is not None:
            self._emit(
                event_type="vision_init",
                payload={"domain": domain, "guided": guided},
            )
        return record

    def update_vision(
        self,
        north_star: str,
        reason: str | None = None,
    ) -> VisionRecord:
        existing = self.load()
        if existing is None:
            raise FileNotFoundError(
                f"No vision record found at {self._vision_path}. Run 'devcd vision init' first."
            )
        now = datetime.now(UTC)
        history_entry = NorthStarVersion(
            statement=existing.north_star,
            replaced_at=now,
            replaced_by_reason=reason,
        )
        updated_history = [history_entry, *existing.history][:_HISTORY_MAX]
        updated = existing.model_copy(
            update={
                "north_star": north_star.strip() if north_star.strip() else existing.north_star,
                "updated_at": now,
                "history": updated_history,
            }
        )
        # north_star blank check is handled by VisionRecord validator on model_copy
        if not north_star.strip():
            raise ValueError("north_star must not be blank or whitespace-only")
        self.save(updated)
        if self._event_ledger is not None:
            self._emit(
                event_type="vision_update",
                payload={"reason": reason},
            )
        return updated

    def get_block(
        self,
        policy_engine: PolicyEngine,
        surface: str = "agent",
    ) -> VisionBlock | None:
        record = self.load()
        if record is None:
            return None
        decision = policy_engine.decide_vision_inject(surface)
        if not decision.allowed:
            return None
        return VisionBlock(
            domain=record.domain,
            north_star=record.north_star,
            active_since=record.updated_at,
            policy_reason=decision.reason,
            withheld=False,
        )

    def assess_alignment(
        self,
        policy_engine: PolicyEngine,
        *,
        surface: str = "agent",
        current_goal: str | None,
        next_action: str | None,
    ) -> VisionAlignmentSignal:
        record = self.load()
        if record is None:
            return VisionAlignmentSignal(note="No vision configured for this workspace.")

        decision = policy_engine.decide_vision_inject(surface)
        if not decision.allowed:
            return VisionAlignmentSignal(
                configured=True,
                visible_to_surface=False,
                status="withheld",
                note="Vision is configured but withheld from this surface by policy.",
            )

        if not current_goal and not next_action:
            return VisionAlignmentSignal(
                configured=True,
                visible_to_surface=True,
                status="configured",
                note=(
                    "Vision is configured for this surface, but alignment needs a current "
                    "goal or next action."
                ),
            )

        keywords = self._alignment_terms(record.north_star)
        if not keywords:
            return VisionAlignmentSignal(
                configured=True,
                visible_to_surface=True,
                status="configured",
                note=(
                    "Vision is configured for this surface, but alignment could not be "
                    "assessed safely from the current North Star text."
                ),
            )

        goal_overlap = bool(keywords & self._alignment_terms(current_goal or ""))
        action_overlap = bool(keywords & self._alignment_terms(next_action or ""))
        if goal_overlap or action_overlap:
            return VisionAlignmentSignal(
                configured=True,
                visible_to_surface=True,
                status="aligned",
                note="Vision is configured and the current goal or next action still reflects it.",
            )

        warning = (
            "Configured vision appears weakly aligned with both the current goal and next action. "
            "Reconfirm the next step against the workspace North Star."
        )
        return VisionAlignmentSignal(
            configured=True,
            visible_to_surface=True,
            status="warn",
            note=(
                "Vision is configured, but the current goal and next action appear to drift "
                "from it."
            ),
            warnings=[warning],
        )

    @staticmethod
    def check_for_sensitive_content(text: str) -> list[str]:
        warnings: list[str] = []
        for pattern in _SENSITIVE_PATTERNS:
            if pattern.search(text):
                if pattern == _SENSITIVE_PATTERNS[1]:
                    warnings.append(
                        "Vision text appears to contain an email address. "
                        "Consider removing personal data before saving."
                    )
                elif pattern == _SENSITIVE_PATTERNS[2]:
                    warnings.append(
                        "Vision text appears to contain URL credentials. "
                        "Remove secrets before saving."
                    )
                else:
                    warnings.append(
                        "Vision text appears to contain a long token or credential. "
                        "Remove secrets before saving."
                    )
        return warnings

    def _emit(self, event_type: str, payload: dict) -> None:  # type: ignore[type-arg]
        if self._event_ledger is None:
            return
        from devcd.slices.policy_layer.models import PolicyDecision, PolicyDecisionKind

        event = DevEvent(
            source=EventSource.SYSTEM,
            type=event_type,
            payload=payload,
        )
        decision = PolicyDecision(
            kind=PolicyDecisionKind.ALLOW,
            reason="vision lifecycle events are always recorded",
            operation=event_type,
        )
        self._event_ledger.append(event, decision)

    @staticmethod
    def _alignment_terms(text: str) -> set[str]:
        return {
            token
            for token in _ALIGNMENT_TOKEN_PATTERN.findall(text.lower())
            if len(token) >= 4 and token not in _ALIGNMENT_STOP_WORDS
        }
