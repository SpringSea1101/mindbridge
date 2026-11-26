from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.config import Settings

if TYPE_CHECKING:
    from app.agents.event_driven_runtime import EventDrivenAgentRuntimeService


def create_agent_runtime(db: Session, settings: Settings) -> EventDrivenAgentRuntimeService:
    # runtime 在这里可以理解为“组织本轮多个 Agent 工作的执行器
    from app.agents.event_driven_runtime import EventDrivenAgentRuntimeService

    return EventDrivenAgentRuntimeService(db, settings)


def agent_framework_status(settings: Settings) -> dict:
    requested = settings.agent_framework.lower()
    active = "event_driven_multi_agent"
    aliases = {"event_driven_multi_agent", "multi_agent", "actors"}
    return {
        "requested": requested,
        "active": active,
        "available": ["event_driven_multi_agent"],
        "fallback": requested not in aliases,
    }
