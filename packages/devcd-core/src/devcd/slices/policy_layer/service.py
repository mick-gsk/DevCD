from __future__ import annotations

from collections.abc import Iterable

from devcd.kernel.settings import DevCDSettings
from devcd.slices.events.models import DevEvent, EventSensitivity
from devcd.slices.policy_layer.models import (
    PolicyDecision,
    PolicyDecisionExplanation,
    PolicyDecisionKind,
    PolicySimulationReport,
)


class PolicyEngine:
    def __init__(
        self,
        allow_observation: bool,
        allow_local_storage: bool,
        allow_remote_export: bool,
        allow_actions: bool,
        enabled_sources: set[str] | None = None,
        allowed_data_classes: set[str] | None = None,
        allow_agentic_context_runs: bool = False,
        agentic_context_runners: list[dict[str, object]] | None = None,
    ) -> None:
        self._allow_observation = allow_observation
        self._allow_local_storage = allow_local_storage
        self._allow_remote_export = allow_remote_export
        self._allow_actions = allow_actions
        self._enabled_sources = enabled_sources or {"ide", "git", "task", "notes", "system"}
        self._allowed_data_classes = allowed_data_classes or {"metadata"}
        self._allow_agentic_context_runs = allow_agentic_context_runs
        self._agentic_context_runner_ids = {
            str(runner.get("id"))
            for runner in agentic_context_runners or []
            if runner.get("enabled", True) and runner.get("id")
        }

    @classmethod
    def default(cls) -> PolicyEngine:
        return cls(
            allow_observation=True,
            allow_local_storage=True,
            allow_remote_export=False,
            allow_actions=False,
            enabled_sources={"ide", "git", "task", "notes", "system"},
            allowed_data_classes={"metadata"},
            allow_agentic_context_runs=False,
            agentic_context_runners=[],
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
            allow_agentic_context_runs=settings.allow_agentic_context_runs,
            agentic_context_runners=settings.agentic_context_runners,
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

    def decide_context_export(self, surface: str, data_class: str = "metadata") -> PolicyDecision:
        if data_class not in self._allowed_data_classes:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="data class is not allowed for local context export by policy",
                operation="export",
                source=surface,
                data_class=data_class,
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.ALLOW,
            reason=f"local context export to '{surface}' is allowed by policy",
            operation="export",
            source=surface,
            data_class=data_class,
        )

    def decide_context_control(self, control_name: str) -> PolicyDecision:
        return PolicyDecision(
            kind=PolicyDecisionKind.ALLOW,
            reason=f"local context control '{control_name}' is allowed by policy",
            operation="context_control",
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

    def decide_agentic_runner_start(self, runner_id: str, task_kind: str) -> PolicyDecision:
        if not self._allow_agentic_context_runs:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason=("local scout runner start is denied by the default local-first policy"),
                operation="agentic_runner_start",
                source=runner_id,
                data_class="metadata",
            )
        if runner_id not in self._agentic_context_runner_ids:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason=f"local scout runner '{runner_id}' is not configured or enabled",
                operation="agentic_runner_start",
                source=runner_id,
                data_class="metadata",
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.ALLOW,
            reason=f"local scout runner '{runner_id}' is allowed for task '{task_kind}'",
            operation="agentic_runner_start",
            source=runner_id,
            data_class="metadata",
        )

    def decide_agentic_runner_output_store(self, data_class: str = "metadata") -> PolicyDecision:
        if data_class != "metadata" or "metadata" not in self._allowed_data_classes:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="agentic runner output storage requires metadata-only summaries",
                operation="agentic_runner_output_store",
                data_class=data_class,
            )
        if not self._allow_local_storage:
            return PolicyDecision(
                kind=PolicyDecisionKind.DENY,
                reason="local storage is disabled by policy",
                operation="agentic_runner_output_store",
                data_class=data_class,
            )
        return PolicyDecision(
            kind=PolicyDecisionKind.ALLOW,
            reason="agentic runner metadata summaries may be stored locally by policy",
            operation="agentic_runner_output_store",
            data_class=data_class,
        )

    def explain_decision(
        self,
        decision: PolicyDecision,
        event: DevEvent | None = None,
    ) -> PolicyDecisionExplanation:
        return PolicyDecisionExplanation(
            decision_id=decision.decision_id,
            allowed=decision.allowed,
            kind=decision.kind,
            operation=decision.operation,
            reason=decision.reason,
            category=self._decision_category(decision, event),
            source=decision.source or (event.source.value if event is not None else None),
            data_class=decision.data_class or (event.data_class if event is not None else None),
            safe_summary=self._safe_summary(decision, event),
        )

    def simulate_event(self, surface: str, event: DevEvent) -> PolicySimulationReport:
        decisions: list[PolicyDecisionExplanation] = []
        withheld: list[PolicyDecisionExplanation] = []

        observation = self.decide_observation(event)
        observation_explanation = self.explain_decision(observation, event)
        decisions.append(observation_explanation)
        if not observation.allowed:
            withheld.append(observation_explanation)
            return PolicySimulationReport(
                surface=surface,
                decisions=decisions,
                withheld=withheld,
            )

        export = self.decide_context_export(surface=surface, data_class=event.data_class)
        export_explanation = self.explain_decision(export, event)
        decisions.append(export_explanation)
        if not export.allowed:
            withheld.append(export_explanation)

        return PolicySimulationReport(surface=surface, decisions=decisions, withheld=withheld)

    def is_source_visible(self, source: str | None) -> bool:
        if source is None:
            return True
        return source in self._enabled_sources

    def _decision_category(self, decision: PolicyDecision, event: DevEvent | None) -> str:
        reason = decision.reason.lower()
        if "sensitive" in reason:
            return "sensitivity"
        if "source" in reason:
            return "source"
        if "data class" in reason:
            return "data_class"
        if "full-text" in reason or "payload" in reason:
            return "payload_content"
        if event is not None:
            return event.data_class
        return decision.operation

    def _safe_summary(self, decision: PolicyDecision, event: DevEvent | None) -> str:
        if decision.allowed:
            return "Context is visible under the selected policy."
        if event is not None:
            return (
                f"{event.source.value} {event.type} signal was withheld; "
                "only source/type metadata is visible as a safe replacement."
            )
        if "data class" in decision.reason.lower():
            return "Metadata-only context may be requested instead."
        return "Context was withheld; no safe replacement is available."

    def _contains_fulltext(self, payload_items: Iterable[tuple[str, object]]) -> bool:
        for key, value in payload_items:
            if key in {"content", "body", "text", "full_text"}:
                return True
            if isinstance(value, str) and len(value) > 512:
                return True
        return False
