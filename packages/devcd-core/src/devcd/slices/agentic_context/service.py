from __future__ import annotations

from devcd.slices.agentic_context.models import (
    ActionPacket,
    ActionPacketBlocker,
    ActionPacketWithheldContext,
    RejectedPath,
    ScoutEvidence,
    ScoutReport,
    ScoutTask,
    ScoutTaskKind,
    SessionContract,
)
from devcd.slices.ambient_context.models import (
    AgentContextSurface,
    ContinuityBlocker,
    ContinuityPacket,
    EvidenceItem,
    SurfaceKind,
    WithheldContext,
)
from devcd.slices.ambient_context.service import AmbientContextService
from devcd.slices.events.ledger import EventLedger
from devcd.slices.events.models import DevEvent, EventSource
from devcd.slices.memory_layer.models import MemoryEntry, MemoryScope
from devcd.slices.policy_layer.models import PolicyDecision, PolicyDecisionKind
from devcd.slices.policy_layer.service import PolicyEngine
from devcd.slices.vision_layer.service import VisionService


class AgenticContextService:
    def __init__(
        self,
        ambient_context_service: AmbientContextService,
        policy_engine: PolicyEngine,
        vision_service: VisionService | None = None,
        event_ledger: EventLedger | None = None,
    ) -> None:
        self.ambient_context_service = ambient_context_service
        self.policy_engine = policy_engine
        self._vision_service = vision_service
        self._event_ledger = event_ledger
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
        persisted_passport = self._load_most_recent_persisted_passport(
            current_packet=packet,
        )
        next_action = self._resolve_warm_start_next_action(persisted_passport)
        if next_action is None and packet.session_contract is not None:
            next_action = packet.session_contract.next_action
        report_evidence = [evidence for report in self._reports for evidence in report.evidence]
        latest_report = self._reports[-1] if self._reports else None
        if latest_report is not None:
            next_action = latest_report.next_action or latest_report.summary
        done_when = self._resolve_done_when()
        verification_required = not bool(done_when)
        rejected_paths = self._rejected_paths_from_memory()
        inherited_next_action = (
            packet.session_contract.next_action if packet.session_contract is not None else ""
        )
        session_contract = SessionContract(
            next_action=next_action or inherited_next_action,
            done_when=done_when or "",
            verification_required=verification_required,
            withheld_count=packet.context_budget.withheld_context_count,
        )
        action_packet = ActionPacket(
            current_goal=current_goal,
            next_action=next_action,
            recommended_agent_mode=self._recommended_agent_mode(packet),
            evidence=[*self._evidence_from_packet(packet), *report_evidence],
            blockers=[self._action_blocker(blocker) for blocker in packet.blockers[:20]],
            do_not_repeat=packet.do_not_repeat[:20],
            context_references=packet.context_references[:30],
            context_budget=packet.context_budget,
            session_contract=session_contract,
            rejected_paths=rejected_paths,
            verification_required=verification_required,
            withheld_context=[
                self._action_withheld_context(withheld) for withheld in packet.withheld_context[:20]
            ],
            policy_summary=packet.policy_decision.reason,
        )
        if self._vision_service is not None:
            workspace_root = getattr(self.ambient_context_service, "_repo_path", None)
            vision_block, _vision_code = self._vision_service.resolve_block(
                self.policy_engine,
                surface=surface,
                active_goal=current_goal,
                workspace_root=workspace_root,
            )
            action_packet = action_packet.model_copy(update={"vision": vision_block})
            if self._event_ledger is not None:
                decision_kind = (
                    PolicyDecisionKind.ALLOW
                    if vision_block is not None
                    else PolicyDecisionKind.DENY
                )
                self._event_ledger.append(
                    DevEvent(
                        source=EventSource.SYSTEM,
                        type="vision_injected",
                        payload={"surface": "action_packet", "allowed": vision_block is not None},
                    ),
                    PolicyDecision(
                        kind=decision_kind,
                        reason="vision injection event",
                        operation="vision_injected",
                    ),
                )
        return action_packet

    def _load_most_recent_persisted_passport(
        self,
        *,
        current_packet: ContinuityPacket,
    ) -> ContinuityPacket | None:
        if self._event_ledger is None:
            return None
        if (
            not self._event_ledger.read_records()
            and not self._event_ledger.read_subtask_completion_events()
        ):
            return None
        return current_packet

    def _resolve_warm_start_next_action(
        self, persisted_passport: ContinuityPacket | None
    ) -> str | None:
        if persisted_passport is None:
            return None
        priority_queue = persisted_passport.priority_queue
        if not priority_queue:
            return None
        if self._event_ledger is None:
            return None
        completed_subtasks = {
            event.subtask_id
            for event in self._event_ledger.read_subtask_completion_events()
            if event.status == "complete"
        }
        for subtask_id in priority_queue:
            if subtask_id not in completed_subtasks:
                return subtask_id
        return None

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

    def _action_blocker(self, blocker: ContinuityBlocker) -> ActionPacketBlocker:
        return ActionPacketBlocker(
            kind=blocker.kind,
            summary=blocker.summary,
            reason=blocker.reason,
            policy_reason=blocker.policy_reason,
        )

    def _action_withheld_context(self, withheld: WithheldContext) -> ActionPacketWithheldContext:
        policy_reason = (
            withheld.policy_reason or withheld.reason or "context was withheld by policy"
        )
        safe_summary = withheld.safe_summary or withheld.reason or "Context was withheld by policy."
        return ActionPacketWithheldContext(
            kind=withheld.kind or "withheld",
            category=withheld.category or withheld.kind or "policy",
            policy_reason=policy_reason,
            safe_summary=safe_summary,
        )

    def _visible_working_memory(self) -> list[MemoryEntry]:
        return self.ambient_context_service.memory_store.list_by_scope(
            MemoryScope.WORKING,
            self.ambient_context_service.state_engine.is_source_visible,
        )

    def _resolve_done_when(self) -> str:
        for entry in self._visible_working_memory():
            event_class = entry.content.get("event_class")
            if event_class != "goal.done_when":
                continue
            payload = entry.content.get("payload")
            if not isinstance(payload, dict):
                continue
            done_when = payload.get("done_when")
            if isinstance(done_when, str) and done_when.strip():
                return done_when
        return ""

    def _rejected_paths_from_memory(self) -> list[RejectedPath]:
        rejected: list[RejectedPath] = []
        for entry in self._visible_working_memory():
            event_class = entry.content.get("event_class")
            if event_class != "dead_end":
                continue
            payload = entry.content.get("payload")
            if not isinstance(payload, dict):
                continue
            approach_summary = payload.get("approach_summary")
            reason = payload.get("reason")
            if not isinstance(approach_summary, str) or not approach_summary.strip():
                continue
            if not isinstance(reason, str) or not reason.strip():
                continue
            rejected.append(
                RejectedPath(
                    approach_summary=approach_summary,
                    reason=reason,
                    timestamp=entry.timestamp,
                )
            )
            if len(rejected) == 20:
                break
        return rejected
