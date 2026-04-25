from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import BaseModel, Field


AgentName = Literal["manager", "engineer", "monitor"]
ActionName = Literal[
    "triage_backlog",
    "assign_bugfix",
    "assign_investigation",
    "reprioritize",
    "scan_logs",
    "alert_incident",
    "verify_fix",
    "inspect_code",
    "implement_fix",
    "write_test",
    "report_blocker",
    "claim_done",
    "idle",
]


class HistoryEntry(BaseModel):
    step: int = Field(ge=0, description="Step index when the action was taken")
    agent: AgentName = Field(description="Agent taking the action on this step")
    action: ActionName = Field(description="Action selected at this step")
    reward: float = Field(ge=0.0, le=1.0, description="Reward assigned for the step")
    cheating_or_hallucination: bool = Field(
        default=False,
        description="True when action made unsupported or deceptive claims",
    )
    note: str = Field(default="", max_length=280, description="Operator note for audit")


class IncidentAction(Action):
    agent: AgentName = Field(description="Agent identity producing this action")
    action: ActionName = Field(description="Incident response action to execute")
    note: str = Field(
        default="",
        max_length=280,
        description="Optional operator note or reasoning trace for the action",
    )


class IncidentObservation(Observation):
    task_id: str = Field(description="Identifier for the active task")
    logs: Dict[str, Any] = Field(description="Current log payload visible to the agent")
    turn_agent: AgentName = Field(description="Agent expected to act on this step")
    step: int = Field(ge=0, description="Current episode step")
    max_steps: int = Field(ge=1, description="Maximum number of steps in the episode")
    remaining_steps: int = Field(
        ge=0, description="Steps remaining before the episode terminates"
    )
    incident_detected: bool = Field(description="Whether the monitoring agent found incident")
    assignment_ready: bool = Field(description="Whether manager assigned executable work")
    patch_ready: bool = Field(description="Whether engineer produced a concrete patch")
    tests_green: bool = Field(description="Whether verification tests are currently passing")
    resolved: bool = Field(description="Whether the outage is resolved")
    schema_drifted: bool = Field(
        description="Whether the log payload has drifted to the alternate schema"
    )
    valid_actions: List[ActionName] = Field(description="Allowed actions for current turn agent")
    team_rewards: Dict[AgentName, float] = Field(
        description="Cumulative reward per agent in [0,1]"
    )
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
    incident_detected: bool = Field(description="Whether monitor has detected incident")
    assignment_ready: bool = Field(description="Whether manager assigned work")
    patch_ready: bool = Field(description="Whether engineer produced fix")
    tests_green: bool = Field(description="Whether verification tests passed")
    schema_drifted: bool = Field(description="Whether the schema drift has occurred")
    done_reason: str = Field(description="Terminal condition or progress marker")
    cumulative_reward: float = Field(
        ge=0.0, description="Sum of rewards earned in the episode"
    )
    current_logs: Dict[str, Any] = Field(description="Current log payload")
    valid_actions: Dict[AgentName, List[ActionName]] = Field(
        description="Allowed actions by agent role"
    )
    turn_agent: AgentName = Field(description="Agent expected to act next")
    team_rewards: Dict[AgentName, float] = Field(
        description="Cumulative reward ledger per agent"
    )
    hallucination_count: int = Field(ge=0, description="Total hallucination/cheating events")
    history: List[HistoryEntry] = Field(
        default_factory=list, description="Step-by-step action history"
    )
    last_action_error: Optional[str] = Field(
        default=None,
        description="Last action error emitted by the environment, if any",
    )
