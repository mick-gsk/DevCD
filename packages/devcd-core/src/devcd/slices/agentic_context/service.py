from __future__ import annotations

from devcd.slices.agentic_context.models import (
    ActionPacket,
    ScoutEvidence,
    ScoutReport,
    ScoutTask,
    ScoutTaskKind,
)
from devcd.slices.ambient_context.models import (
    AgentContextSurface,
    ContinuityPacket,
    EvidenceItem,
    SurfaceKind,
)
from devcd.slices.ambient_context.service import AmbientContextService
from devcd.slices.policy_layer.service import PolicyEngine


class AgenticContextService:
    def __init__(
        self,
        ambient_context_service: AmbientContextService,
        policy_engine: PolicyEngine,
    ) -> None:
        self.ambient_context_service = ambient_context_service
        self.policy_engine = policy_engine
        self._reports: list[ScoutReport] = []

    def create_scout_tasks(
        self,
        *,
        surface: str = "coding-agent",
        context_pack: str = "developer",
    ) -> list[ScoutTask]:
        decision = self.policy_engine.decide_context_export(surface=surface, data_class="metadata")
        if not decision.allowed:
            raise ValueError(decision.reason)
        prompts = {
            ScoutTaskKind.IDENTIFY_CURRENT_GOAL: (
                "Identify the active goal from visible local metadata."
            ),
            ScoutTaskKind.FIND_RELEVANT_ARTIFACTS: (
                "Find the most relevant artifacts from policy-visible continuity metadata."
            ),
            ScoutTaskKind.SUMMARIZE_BLOCKERS: (
                "Summarize blockers and failed attempts from visible continuity metadata."
            ),
            ScoutTaskKind.PROPOSE_NEXT_ACTION: (
                "Propose the next safe action for the next agent run."
            ),
        }
        return [
            ScoutTask(
                kind=kind,
                prompt=prompt,
                surface=surface,
                context_pack=context_pack,
                expected_evidence=["devcd_continuity"],
                policy_decision_id=decision.decision_id,
            )
            for kind, prompt in prompts.items()
        ]

    def create_action_packet(
        self,
        *,
        surface: str = "coding-agent",
        context_pack: str = "developer",
    ) -> ActionPacket:
        packet = self.ambient_context_service.create_continuity_packet(
            AgentContextSurface(kind=SurfaceKind(surface)),
            context_pack=context_pack,
            include_empty_guidance=True,
        )
        current_goal = packet.intent.summary if packet.intent is not None else None
        next_action = packet.suggested_next_steps[0] if packet.suggested_next_steps else None
        if current_goal is not None and next_action is None:
            next_action = "Use Scout Tasks to identify the next safe action."
        report_evidence = [evidence for report in self._reports for evidence in report.evidence]
        latest_report = self._reports[-1] if self._reports else None
        if latest_report is not None:
            next_action = latest_report.next_action or latest_report.summary
        return ActionPacket(
            current_goal=current_goal,
            next_action=next_action,
            recommended_agent_mode=self._recommended_agent_mode(packet),
            evidence=[*self._evidence_from_packet(packet), *report_evidence],
            policy_summary=packet.policy_decision.reason,
        )

    def accept_scout_report(self, report: ScoutReport) -> ScoutReport:
        if not report.evidence:
            raise ValueError("scout reports require evidence")
        storage_decision = self.policy_engine.decide_agentic_runner_output_store(
            data_class=report.data_class,
        )
        if not storage_decision.allowed:
            raise ValueError(storage_decision.reason)
        accepted = report.model_copy(deep=True)
        self._reports.append(accepted)
        return accepted

    def _recommended_agent_mode(self, packet: ContinuityPacket) -> str:
        if packet.blockers:
            return "debugging"
        if packet.intent is not None:
            return "implementation"
        return "context-scout"

    def _evidence_from_packet(self, packet: ContinuityPacket) -> list[ScoutEvidence]:
        evidence: list[ScoutEvidence] = []
        if packet.intent is not None:
            evidence.extend(self._scout_evidence(item) for item in packet.intent.evidence)
            if not evidence:
                evidence.append(
                    ScoutEvidence(
                        source="devcd",
                        summary="Continuity packet identified the active goal.",
                        timestamp=packet.generated_at,
                        policy_reason=packet.policy_decision.reason,
                    )
                )
        for blocker in packet.blockers:
            evidence.extend(self._scout_evidence(item) for item in blocker.evidence)
        return evidence

    def _scout_evidence(self, evidence: EvidenceItem) -> ScoutEvidence:
        return ScoutEvidence(
            source=evidence.source,
            summary=evidence.summary,
            timestamp=evidence.timestamp,
            policy_reason=evidence.policy_reason,
        )