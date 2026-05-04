from __future__ import annotations

from collections.abc import Iterable

from devcd.kernel.settings import DevCDSettings
from devcd.slices.events.models import DevEvent, EventSensitivity
from devcd.slices.policy_layer.models import PolicyDecision, PolicyDecisionKind


class PolicyEngine:
    def __init__(
        self,
        allow_observation: bool,
        allow_local_storage: bool,
        allow_remote_export: bool,
        allow_actions: bool,
        enabled_sources: set[str] | None = None,
        allowed_data_classes: set[str] | None = None,
    ) -> None:
        self._allow_observation = allow_observation
        self._allow_local_storage = allow_local_storage
        self._allow_remote_export = allow_remote_export
        self._allow_actions = allow_actions
        self._enabled_sources = enabled_sources or {"ide", "git", "task", "notes", "system"}
        self._allowed_data_classes = allowed_data_classes or {"metadata"}

    @classmethod
    def default(cls) -> PolicyEngine:
        return cls(
            allow_observation=True,
            allow_local_storage=True,
            allow_remote_export=False,
            allow_actions=False,
            enabled_sources={"ide", "git", "task", "notes", "system"},
            allowed_data_classes={"metadata"},
        )

    @classmethod
    def from_settings(cls, settings: DevCDSettings) -> PolicyEngine:
        return cls(
            allow_observation=settings.allow_observation,
            allow_local_storage=settings.allow_local_storage,
            allow_remote_export=settings.allow_remote_export,
            allow_actions=settings.allow_actions,
            enabled_sources=settings.enabled_sources,
            allowed_data_classes=settings.allowed_data_classes,
        )

    def decide_observation(self, event: DevEvent) -> PolicyDecision:
        if event.source.value not in self._enabled_sources:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="source is not enabled by policy",
                operation="observe",
                source=event.source.value,
                data_class=event.data_class,
            )
        if event.data_class not in self._allowed_data_classes:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="data class is not allowed by policy",
                operation="observe",
                source=event.source.value,
                data_class=event.data_class,
            )
        if self._contains_fulltext(event.payload.items()):
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="metadata-only policy denied full-text payload content",
                operation="observe",
                source=event.source.value,
                data_class=event.data_class,
            )
        if event.sensitivity is EventSensitivity.SENSITIVE:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="sensitive events are denied by the default local policy",
                operation="observe",
                source=event.source.value,
                data_class=event.data_class,
            )
        if self._allow_observation:
            return PolicyDecision(
                kind=PolicyDecisionKind.ALLOW,
                reason="observation is allowed by the default local policy",
                operation="observe",
                source=event.source.value,
                data_class=event.data_class,
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.DENY,
            reason="observation is disabled by policy",
            operation="observe",
            source=event.source.value,
            data_class=event.data_class,
        )

    def decide_local_storage(self, event: DevEvent) -> PolicyDecision:
        if event.sensitivity is EventSensitivity.SENSITIVE:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="sensitive events are not persisted by the default local policy",
                operation="store",
                source=event.source.value,
                data_class=event.data_class,
            )
        if self._allow_local_storage:
            return PolicyDecision(
                kind=PolicyDecisionKind.ALLOW,
                reason="local storage is allowed by policy",
                operation="store",
                source=event.source.value,
                data_class=event.data_class,
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.DENY,
            reason="local storage is disabled by policy",
            operation="store",
            source=event.source.value,
            data_class=event.data_class,
        )

    def decide_remote_export(self, destination: str) -> PolicyDecision:
        if self._allow_remote_export:
            return PolicyDecision(
                kind=PolicyDecisionKind.ALLOW,
                reason=f"remote export to '{destination}' is allowed by policy",
                operation="export",
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.DENY,
            reason=f"remote export to '{destination}' is denied by the default local-first policy",
            operation="export",
        )

    def decide_action(self, action_name: str) -> PolicyDecision:
        if self._allow_actions:
            return PolicyDecision(
                kind=PolicyDecisionKind.ALLOW,
                reason=f"action '{action_name}' is allowed by policy",
                operation="action",
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.DENY,
            reason=f"action '{action_name}' is denied by the default observe-only policy",
            operation="action",
        )

    def is_source_visible(self, source: str | None) -> bool:
        if source is None:
            return True
        return source in self._enabled_sources

    def _contains_fulltext(self, payload_items: Iterable[tuple[str, object]]) -> bool:
        for key, value in payload_items:
            if key in {"content", "body", "text", "full_text"}:
                return True
            if isinstance(value, str) and len(value) > 512:
                return True
        return False
