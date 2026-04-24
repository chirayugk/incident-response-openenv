from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


ActionName = Literal["check_logs", "fix_bug", "ignore"]
Difficulty = Literal["easy", "medium", "hard"]
DoneReason = Literal["in_progress", "resolved", "max_steps_reached", "invalid_action"]


class TaskSpec(BaseModel):
    task_id: str
    title: str
    difficulty: Difficulty = "easy"
    description: str
    objective: str
    max_steps: int = Field(ge=1)


class HistoryEntry(BaseModel):
    step: int = Field(ge=0)
    action: ActionName
    reward: float = Field(ge=0.0, le=1.0)
    resolved_after_action: bool


class Observation(BaseModel):
    logs: Dict[str, Any]
    step: int = Field(ge=0)
    max_steps: int = Field(ge=1)
    remaining_steps: int = Field(ge=0)
    resolved: bool
    schema_drifted: bool
    valid_actions: List[ActionName]
    last_action: Optional[ActionName] = None
    history_length: int = Field(ge=0)

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)


class State(BaseModel):
    logs: Dict[str, Any]
    step: int
    resolved: bool


class Action(BaseModel):
    action: ActionName


class StepInfo(BaseModel):
    resolved: bool
    step: int = Field(ge=0)
    max_steps: int = Field(ge=1)
    remaining_steps: int = Field(ge=0)
    schema_drifted: bool
    done_reason: DoneReason
    last_action_error: Optional[str] = None


class StepResult(BaseModel):
    observation: Observation
    reward: float = Field(ge=0.0, le=1.0)
    done: bool
    info: StepInfo


class ResetRequest(BaseModel):
    task_id: str = Field(default="incident_response_easy")
    seed: int = Field(default=7, ge=0)
    max_episode_steps: Optional[int] = Field(default=None, ge=1, le=64)


class ResetResponse(BaseModel):
    observation: Observation
    info: Dict[str, Any]


class StateSnapshot(BaseModel):
    task: TaskSpec
    step: int = Field(ge=0)
    max_steps: int = Field(ge=1)
    done: bool
    resolved: bool
    schema_drifted: bool
    done_reason: DoneReason
    cumulative_reward: float = Field(ge=0.0)
    current_logs: Dict[str, Any]
    history: List[HistoryEntry]
    last_action_error: Optional[str] = None


class StateResponse(BaseModel):
    state: StateSnapshot


class MetadataResponse(BaseModel):
    name: str
    description: str
    benchmark: str
    version: str
    rewards_range: List[float]
    tasks: List[TaskSpec]


class SchemaResponse(BaseModel):
    action: Dict[str, Any]
    observation: Dict[str, Any]
    state: Dict[str, Any]


class TasksResponse(BaseModel):
    tasks: List[TaskSpec]
