from datetime import UTC, datetime
from enum import Enum
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    run_started = "run_started"
    run_completed = "run_completed"
    agent_started = "agent_started"
    agent_completed = "agent_completed"
    tool_called = "tool_called"
    policy_checked = "policy_checked"
    approval_requested = "approval_requested"
    approval_granted = "approval_granted"
    approval_rejected = "approval_rejected"
    write_action_executed = "write_action_executed"
    write_action_failed = "write_action_failed"
    policy_violation = "policy_violation"


class AuditEvent(BaseModel):
    event_id: str
    run_id: str
    event_type: AuditEventType
    actor: str
    details: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))