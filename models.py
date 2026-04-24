from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import BaseModel, Field


ActionName = Literal["check_logs", "fix_bug", "ignore"]


class HistoryEntry(BaseModel):
    step: int = Field(ge=0, description="Step index when the action was taken")
    action: ActionName = Field(description="Action selected at this step")
    reward: float = Field(ge=0.0, le=1.0, description="Reward assigned for the step")
    resolved_after_action: bool = Field(
        description="Whether the incident was resolved after this action"
    )


class IncidentAction(Action):
    action: ActionName = Field(description="Incident response action to execute")
    note: str = Field(
        default="",
        max_length=280,
        description="Optional operator note or reasoning trace for the action",
    )


class IncidentObservation(Observation):
    task_id: str = Field(description="Identifier for the active task")
    logs: Dict[str, Any] = Field(description="Current log payload visible to the agent")
    step: int = Field(ge=0, description="Current episode step")
    max_steps: int = Field(ge=1, description="Maximum number of steps in the episode")
    remaining_steps: int = Field(
        ge=0, description="Steps remaining before the episode terminates"
    )
    resolved: bool = Field(description="Whether the outage is resolved")
    schema_drifted: bool = Field(
        description="Whether the log payload has drifted to the alternate schema"
    )
    valid_actions: List[ActionName] = Field(description="Allowed actions for the agent")
    last_action: Optional[ActionName] = Field(
        default=None,
        description="Most recent action that led to this observation",
    )
    history_length: int = Field(
        ge=0, description="Number of actions taken so far in the episode"
    )


class IncidentState(State):
    task_id: str = Field(description="Identifier for the current task")
    seed: Optional[int] = Field(default=None, ge=0, description="Reset seed, if provided")
    max_steps: int = Field(ge=1, description="Maximum steps configured for the episode")
    resolved: bool = Field(description="Whether the incident has been resolved")
    done: bool = Field(description="Whether the episode is terminal")
    schema_drifted: bool = Field(description="Whether the schema drift has occurred")
    done_reason: str = Field(description="Terminal condition or progress marker")
    cumulative_reward: float = Field(
        ge=0.0, description="Sum of rewards earned in the episode"
    )
    current_logs: Dict[str, Any] = Field(description="Current log payload")
    valid_actions: List[ActionName] = Field(description="Allowed actions")
    history: List[HistoryEntry] = Field(
        default_factory=list, description="Step-by-step action history"
    )
    last_action_error: Optional[str] = Field(
        default=None,
        description="Last action error emitted by the environment, if any",
    )
