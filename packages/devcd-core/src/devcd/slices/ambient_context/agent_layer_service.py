from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

import tomli_w

from devcd.kernel.settings import DevCDSettings
from devcd.slices.ambient_context.agent_layer_models import (
    AgentDetectionStatus,
    AgentLayerApplyResult,
    AgentLayerArchetype,
    AgentLayerArchetypeDefinition,
    AgentLayerProfile,
    AgentLayerProfileLoadResult,
    AgentLayerProposal,
    AgentLayerWritePreview,
    AgentTarget,
    DetectedAgentTarget,
    DetectedWorkspaceTool,
    WorkspaceDetectionResult,
    WorkspaceToolKind,
)
from devcd.slices.events.models import DevEvent, EventSource
from devcd.slices.policy_layer.service import PolicyEngine

AGENT_LAYER_PROFILE_PATH = Path(".devcd") / "agent-layer-profile.json"

_AGENT_DISPLAY_NAMES: dict[AgentTarget, str] = {
    AgentTarget.COPILOT: "Copilot",
    AgentTarget.CLAUDE: "Claude",
    AgentTarget.CODEX: "Codex",
    AgentTarget.OPENCLAW: "OpenClaw",
}

_AGENT_INSTRUCTION_PATHS: dict[AgentTarget, Path] = {
    AgentTarget.COPILOT: Path(".github") / "copilot-instructions.md",
    AgentTarget.CLAUDE: Path("CLAUDE.md"),
    AgentTarget.CODEX: Path("AGENTS.md"),
    AgentTarget.OPENCLAW: Path(".devcd") / "openclaw-mcp.json",
}

_COPILOT_INSTRUCTION_CANDIDATE_PATHS: tuple[Path, ...] = (
    Path(".github") / "instructions" / "copilot.instructions.md",
    Path(".github") / "copilot-instructions.md",
)

_DEVCD_AGENT_BLOCK_START = "<!-- DEVCD AGENT CONTINUITY START -->"
_DEVCD_AGENT_BLOCK_END = "<!-- DEVCD AGENT CONTINUITY END -->"

_MAX_CONTEXT_CHARS = 8000
_CONTINUITY_BLOCK_MAX_CHARS = 4000


class AgentLayerService:
    def __init__(self, settings: DevCDSettings, policy_engine: PolicyEngine) -> None:
        self._settings = settings
        self._policy_engine = policy_engine

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    def load_profile(self) -> AgentLayerProfileLoadResult:
        profile_path = AGENT_LAYER_PROFILE_PATH
        if not profile_path.exists():
            return AgentLayerProfileLoadResult(
                profile=AgentLayerProfile(targets=[], archetypes=[]),
                path=profile_path,
                existed=False,
            )
        with profile_path.open() as f:
            data = json.load(f)
        return AgentLayerProfileLoadResult(
            profile=AgentLayerProfile(
                targets=[AgentTarget(t) for t in data.get("targets", [])],
                archetypes=[
                    AgentLayerArchetype(
                        name=a["name"],
                        definition=AgentLayerArchetypeDefinition(**a["definition"]),
                    )
                    for a in data.get("archetypes", [])
                ],
            ),
            path=profile_path,
            existed=True,
        )

    def save_profile(self, profile: AgentLayerProfile) -> None:
        profile_path = AGENT_LAYER_PROFILE_PATH
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        with profile_path.open("w") as f:
            json.dump(
                {
                    "targets": [t.value for t in profile.targets],
                    "archetypes": [
                        {
                            "name": a.name,
                            "definition": {
                                "description": a.definition.description,
                                "tools": a.definition.tools,
                            },
                        }
                        for a in profile.archetypes
                    ],
                },
                f,
                indent=2,
            )
            f.write("\n")

    # ------------------------------------------------------------------
    # Workspace detection
    # ------------------------------------------------------------------

    def detect_workspace(self) -> WorkspaceDetectionResult:
        detected_tools: list[DetectedWorkspaceTool] = []
        for tool_kind in WorkspaceToolKind:
            if self._detect_tool(tool_kind):
                detected_tools.append(
                    DetectedWorkspaceTool(
                        kind=tool_kind,
                        config_path=self._tool_config_path(tool_kind),
                    )
                )
        detected_agents: list[DetectedAgentTarget] = []
        for target in AgentTarget:
            status, path = self._detect_agent(target)
            detected_agents.append(
                DetectedAgentTarget(
                    target=target,
                    status=status,
                    instruction_path=path,
                )
            )
        return WorkspaceDetectionResult(
            tools=detected_tools,
            agents=detected_agents,
        )

    def _detect_tool(self, tool_kind: WorkspaceToolKind) -> bool:
        config_path = self._tool_config_path(tool_kind)
        return config_path is not None and config_path.exists()

    def _tool_config_path(self, tool_kind: WorkspaceToolKind) -> Path | None:
        if tool_kind == WorkspaceToolKind.PYPROJECT:
            return Path("pyproject.toml") if Path("pyproject.toml").exists() else None
        if tool_kind == WorkspaceToolKind.PACKAGE_JSON:
            return (
                Path("package.json") if Path("package.json").exists() else None
            )
        return None

    def _detect_agent(
        self, target: AgentTarget
    ) -> tuple[AgentDetectionStatus, Path | None]:
        instruction_path = _AGENT_INSTRUCTION_PATHS.get(target)
        if instruction_path is None:
            return AgentDetectionStatus.NOT_CONFIGURED, None
        if target == AgentTarget.COPILOT:
            for candidate in _COPILOT_INSTRUCTION_CANDIDATE_PATHS:
                if candidate.exists():
                    return AgentDetectionStatus.CONFIGURED, candidate
            return AgentDetectionStatus.NOT_CONFIGURED, None
        if instruction_path.exists():
            return AgentDetectionStatus.CONFIGURED, instruction_path
        return AgentDetectionStatus.NOT_CONFIGURED, None

    # ------------------------------------------------------------------
    # Proposal / preview / apply
    # ------------------------------------------------------------------

    def propose(
        self,
        profile: AgentLayerProfile,
        detection: WorkspaceDetectionResult,
    ) -> AgentLayerProposal:
        changes: list[dict[str, Any]] = []
        for target in profile.targets:
            instruction_path = _AGENT_INSTRUCTION_PATHS.get(target)
            if instruction_path is None:
                continue
            detected = next(
                (a for a in detection.agents if a.target == target), None
            )
            if detected and detected.status == AgentDetectionStatus.CONFIGURED:
                changes.append(
                    {
                        "target": target,
                        "path": instruction_path,
                        "action": "update",
                    }
                )
            else:
                changes.append(
                    {
                        "target": target,
                        "path": instruction_path,
                        "action": "create",
                    }
                )
        return AgentLayerProposal(changes=changes)

    def preview(
        self,
        profile: AgentLayerProfile,
        proposal: AgentLayerProposal,
        context: str,
    ) -> AgentLayerWritePreview:
        previews: list[dict[str, Any]] = []
        for change in proposal.changes:
            target: AgentTarget = change["target"]
            path: Path = change["path"]
            content = self._render_instructions(target, profile, context)
            previews.append(
                {
                    "target": target,
                    "path": path,
                    "action": change["action"],
                    "content": content,
                }
            )
        return AgentLayerWritePreview(previews=previews)

    def apply(
        self,
        preview: AgentLayerWritePreview,
    ) -> AgentLayerApplyResult:
        written: list[Path] = []
        for item in preview.previews:
            path: Path = item["path"]
            content: str = item["content"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            written.append(path)
        return AgentLayerApplyResult(written=written)

    # ------------------------------------------------------------------
    # Context / continuity block helpers
    # ------------------------------------------------------------------

    def build_mcp_context(self, settings: DevCDSettings) -> str:
        """Build a concise MCP context string from settings."""
        parts: list[str] = []
        if settings.project_name:
            parts.append(f"Project: {settings.project_name}")
        if settings.description:
            parts.append(f"Description: {settings.description}")
        context = "\n".join(parts)
        if len(context) > _MAX_CONTEXT_CHARS:
            context = context[:_MAX_CONTEXT_CHARS] + "..."
        return context

    def read_continuity_block(self, target: AgentTarget) -> str | None:
        """Read the devcd continuity block from an agent instruction file."""
        instruction_path = _AGENT_INSTRUCTION_PATHS.get(target)
        if instruction_path is None or not instruction_path.exists():
            return None
        text = instruction_path.read_text()
        start = text.find(_DEVCD_AGENT_BLOCK_START)
        end = text.find(_DEVCD_AGENT_BLOCK_END)
        if start == -1 or end == -1:
            return None
        return text[start + len(_DEVCD_AGENT_BLOCK_START) : end].strip()

    def write_continuity_block(
        self, target: AgentTarget, block_content: str
    ) -> None:
        """Write or replace the devcd continuity block in an agent instruction file."""
        instruction_path = _AGENT_INSTRUCTION_PATHS.get(target)
        if instruction_path is None:
            return
        block_content = block_content[:_CONTINUITY_BLOCK_MAX_CHARS]
        full_block = (
            f"{_DEVCD_AGENT_BLOCK_START}\n{block_content}\n{_DEVCD_AGENT_BLOCK_END}\n"
        )
        if not instruction_path.exists():
            instruction_path.parent.mkdir(parents=True, exist_ok=True)
            instruction_path.write_text(full_block)
            return
        text = instruction_path.read_text()
        start = text.find(_DEVCD_AGENT_BLOCK_START)
        end = text.find(_DEVCD_AGENT_BLOCK_END)
        if start == -1 or end == -1:
            instruction_path.write_text(text.rstrip() + "\n\n" + full_block)
        else:
            new_text = (
                text[:start]
                + full_block
                + text[end + len(_DEVCD_AGENT_BLOCK_END) :].lstrip("\n")
            )
            instruction_path.write_text(new_text)

    # ------------------------------------------------------------------
    # Instruction rendering
    # ------------------------------------------------------------------

    def _render_instructions(
        self,
        target: AgentTarget,
        profile: AgentLayerProfile,
        context: str,
    ) -> str:
        lines: list[str] = [_agent_instructions_header(target)]
        if context:
            lines.append("")
            lines.append("## Project Context")
            lines.append(context)
        for archetype in profile.archetypes:
            lines.append("")
            lines.append(f"## {archetype.name}")
            if archetype.definition.description:
                lines.append(archetype.definition.description)
            if archetype.definition.tools:
                lines.append("")
                lines.append("Tools:")
                for tool in archetype.definition.tools:
                    lines.append(f"- {tool}")
        return "\n".join(lines) + "\n"

    def get_settings(self) -> DevCDSettings:
        """Read settings from pyproject.toml if present."""
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            return self._settings
        with pyproject_path.open("rb") as f:
            data = tomllib.load(f)
        devcd_data = data.get("tool", {}).get("devcd", {})
        if not devcd_data:
            return self._settings
        current = self._settings.model_dump()
        current.update(devcd_data)
        return DevCDSettings(**current)

    def update_settings(self, updates: dict[str, Any]) -> DevCDSettings:
        """Update settings in pyproject.toml."""
        pyproject_path = Path("pyproject.toml")
        if pyproject_path.exists():
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
        else:
            data = {}
        tool_section = data.setdefault("tool", {})
        devcd_section = tool_section.setdefault("devcd", {})
        devcd_section.update(updates)
        with pyproject_path.open("wb") as f:
            tomli_w.dump(data, f)
        return self.get_settings()


def _agent_instructions_header(target: AgentTarget) -> str:
    name = _AGENT_DISPLAY_NAMES.get(target, target.value)
    return f"# {name} Instructions"


def _normalize_agent_target(target: AgentTarget | str) -> AgentTarget:
    if isinstance(target, AgentTarget):
        return target
    return AgentTarget(target)
