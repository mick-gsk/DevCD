from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    AGENT_MESSAGE = "agent_message"
    SYSTEM_MESSAGE = "system_message"
    ERROR = "error"
    CONTEXT_UPDATE = "context_update"


@dataclass
class Event:
    event_type: EventType
    data: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
