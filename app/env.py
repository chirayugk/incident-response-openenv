from __future__ import annotations

from typing import Any, Dict, Optional

from app.models import HistoryEntry, Observation, StateSnapshot, StepInfo, TaskSpec
from app.rewards import compute_reward


DEFAULT_TASK = TaskSpec(
    task_id="incident_response_easy",
    title="Incident Response Drill",
    difficulty="easy",
    description=(
        "Recover a service from a timeout incident while the log schema drifts mid-episode."
    ),
    objective="Inspect the logs, notice the schema drift, and resolve the outage quickly.",
    max_steps=6,
)


class IncidentEnv:
    def __init__(self) -> None:
        self.task = DEFAULT_TASK
        self.valid_actions = ["check_logs", "fix_bug", "ignore"]
        self.reset()

    def reset(
        self,
        task_id: str = DEFAULT_TASK.task_id,
        seed: int = 7,
        max_episode_steps: Optional[int] = None,
    ) -> Observation:
        if task_id != self.task.task_id:
            raise ValueError(f"Unknown task_id '{task_id}'. Supported task: {self.task.task_id}")

        self.seed = seed
        self.max_steps = max_episode_steps or self.task.max_steps
        self.state_data: Dict[str, Any] = {
            "logs": {
                "error": "timeout",
                "service": "checkout-api",
                "region": "ap-south-1",
            },
            "step": 0,
            "resolved": False,
        }
        self.state = self.state_data
        self.history: list[tuple[int, str]] = []
        self.history_entries: list[HistoryEntry] = []
        self.cumulative_reward = 0.0
        self.done = False
        self.done_reason = "in_progress"
        self.last_action_error: Optional[str] = None
        return self.get_observation()

    def _ensure_ready(self) -> None:
        if not hasattr(self, "state_data"):
            self.reset()

    def get_observation(self, last_action: Optional[str] = None) -> Observation:
        self._ensure_ready()
        return Observation(
            logs=self.state_data["logs"],
            step=self.state_data["step"],
            max_steps=self.max_steps,
            remaining_steps=max(self.max_steps - self.state_data["step"], 0),
            resolved=self.state_data["resolved"],
            schema_drifted="code" in self.state_data["logs"],
            valid_actions=list(self.valid_actions),
            last_action=last_action if last_action in self.valid_actions else None,
            history_length=len(self.history_entries),
        )

    def _build_step_info(self) -> StepInfo:
        return StepInfo(
            resolved=self.state_data["resolved"],
            step=self.state_data["step"],
            max_steps=self.max_steps,
            remaining_steps=max(self.max_steps - self.state_data["step"], 0),
            schema_drifted="code" in self.state_data["logs"],
            done_reason=self.done_reason,
            last_action_error=self.last_action_error,
        )

    def step(self, action: str):
        self._ensure_ready()

        if self.done:
            self.last_action_error = "Episode already finished. Reset the environment to start again."
            observation = self.get_observation()
            return observation, 0.0, True, self._build_step_info().model_dump()

        if action not in self.valid_actions:
            self.done = True
            self.done_reason = "invalid_action"
            self.last_action_error = f"Unsupported action: {action}"
            observation = self.get_observation()
            return observation, 0.0, True, self._build_step_info().model_dump()

        self.last_action_error = None
        self.state_data["step"] += 1

        if self.state_data["step"] == 3 and not self.state_data["resolved"]:
            self.state_data["logs"] = {
                "code": 504,
                "message": "gateway timeout",
                "service": "checkout-api",
                "trace_id": "inc-504-demo",
            }

        if action == "fix_bug" and (
            "error" in self.state_data["logs"] or "code" in self.state_data["logs"]
        ):
            self.state_data["resolved"] = True

        history_pairs = list(self.history)
        history_pairs.append((self.state_data["step"], action))
        reward = compute_reward(
            self.state_data,
            action,
            history_pairs,
            self.state_data["step"],
        )

        self.cumulative_reward = round(self.cumulative_reward + reward, 3)
        self.history.append((self.state_data["step"], action))
        self.history_entries.append(
            HistoryEntry(
                step=self.state_data["step"],
                action=action,
                reward=reward,
                resolved_after_action=self.state_data["resolved"],
            )
        )

        self.done = self.state_data["resolved"] or self.state_data["step"] >= self.max_steps
        if self.state_data["resolved"]:
            self.done_reason = "resolved"
        elif self.state_data["step"] >= self.max_steps:
            self.done_reason = "max_steps_reached"
        else:
            self.done_reason = "in_progress"

        observation = self.get_observation(last_action=action)
        return observation, reward, self.done, self._build_step_info().model_dump()

    def snapshot(self) -> StateSnapshot:
        self._ensure_ready()
        return StateSnapshot(
            task=self.task.model_copy(update={"max_steps": self.max_steps}),
            step=self.state_data["step"],
            max_steps=self.max_steps,
            done=self.done,
            resolved=self.state_data["resolved"],
            schema_drifted="code" in self.state_data["logs"],
            done_reason=self.done_reason,
            cumulative_reward=self.cumulative_reward,
            current_logs=self.state_data["logs"],
            history=list(self.history_entries),
            last_action_error=self.last_action_error,
        )
