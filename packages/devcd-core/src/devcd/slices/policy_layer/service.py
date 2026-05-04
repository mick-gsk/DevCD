from __future__ import annotations

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
    ) -> None:
        self._allow_observation = allow_observation
        self._allow_local_storage = allow_local_storage
        self._allow_remote_export = allow_remote_export
        self._allow_actions = allow_actions

    @classmethod
    def default(cls) -> PolicyEngine:
        return cls(
            allow_observation=True,
            allow_local_storage=True,
            allow_remote_export=False,
            allow_actions=False,
        )

    @classmethod
    def from_settings(cls, settings: DevCDSettings) -> PolicyEngine:
        return cls(
            allow_observation=settings.allow_observation,
            allow_local_storage=settings.allow_local_storage,
            allow_remote_export=settings.allow_remote_export,
            allow_actions=settings.allow_actions,
        )

    def decide_observation(self, event: DevEvent) -> PolicyDecision:
        if event.sensitivity is EventSensitivity.SENSITIVE:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="sensitive events are denied by the default local policy",
            )
        if self._allow_observation:
            return PolicyDecision(
                kind=PolicyDecisionKind.ALLOW,
                reason="observation is allowed by the default local policy",
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.DENY,
            reason="observation is disabled by policy",
        )

    def decide_local_storage(self, event: DevEvent) -> PolicyDecision:
        if event.sensitivity is EventSensitivity.SENSITIVE:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="sensitive events are not persisted by the default local policy",
            )
        if self._allow_local_storage:
            return PolicyDecision(
                kind=PolicyDecisionKind.ALLOW,
                reason="local storage is allowed by policy",
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.DENY,
            reason="local storage is disabled by policy",
        )

    def decide_remote_export(self, destination: str) -> PolicyDecision:
        if self._allow_remote_export:
            return PolicyDecision(
                kind=PolicyDecisionKind.ALLOW,
                reason=f"remote export to '{destination}' is allowed by policy",
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.DENY,
            reason=f"remote export to '{destination}' is denied by the default local-first policy",
        )

    def decide_action(self, action_name: str) -> PolicyDecision:
        if self._allow_actions:
            return PolicyDecision(
                kind=PolicyDecisionKind.ALLOW,
                reason=f"action '{action_name}' is allowed by policy",
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.DENY,
            reason=f"action '{action_name}' is denied by the default observe-only policy",
        )
