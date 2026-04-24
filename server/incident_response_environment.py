from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import EnvironmentMetadata

from app.rewards import compute_reward

try:
    from ..models import HistoryEntry, IncidentAction, IncidentObservation, IncidentState
except ImportError:
    from models import HistoryEntry, IncidentAction, IncidentObservation, IncidentState


class IncidentResponseEnvironment(
    Environment[IncidentAction, IncidentObservation, IncidentState]
):
    """OpenEnv-compatible incident response environment with schema drift."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, default_max_steps: int = 6):
        super().__init__()
        self.default_max_steps = default_max_steps
        self.valid_actions = ["check_logs", "fix_bug", "ignore"]
        self.default_task_id = "incident_response_easy"
        self._state = IncidentState(
            episode_id=str(uuid4()),
            step_count=0,
            task_id=self.default_task_id,
            seed=None,
            max_steps=default_max_steps,
            resolved=False,
            done=False,
            schema_drifted=False,
            done_reason="not_started",
            cumulative_reward=0.0,
            current_logs={},
            valid_actions=list(self.valid_actions),
            history=[],
            last_action_error=None,
        )
        self.reset()

    def _initial_logs(self) -> Dict[str, Any]:
        return {
            "error": "timeout",
            "service": "checkout-api",
            "region": "ap-south-1",
        }

    def _build_observation(
        self,
        reward: Optional[float],
        last_action: Optional[str] = None,
    ) -> IncidentObservation:
        return IncidentObservation(
            task_id=self._state.task_id,
            logs=self._state.current_logs,
            step=self._state.step_count,
            max_steps=self._state.max_steps,
            remaining_steps=max(self._state.max_steps - self._state.step_count, 0),
            resolved=self._state.resolved,
            schema_drifted=self._state.schema_drifted,
            valid_actions=list(self.valid_actions),
            last_action=last_action,
            history_length=len(self._state.history),
            done=self._state.done,
            reward=reward,
            metadata={
                "episode_id": self._state.episode_id,
                "done_reason": self._state.done_reason,
                "last_action_error": self._state.last_action_error,
            },
        )

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        task_id: Optional[str] = None,
        max_episode_steps: Optional[int] = None,
        **kwargs: Any,
    ) -> IncidentObservation:
        active_task_id = task_id or self.default_task_id
        if active_task_id != self.default_task_id:
            raise ValueError(
                f"Unknown task_id '{active_task_id}'. Supported task: {self.default_task_id}"
            )

        self._state = IncidentState(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
            task_id=active_task_id,
            seed=seed,
            max_steps=max_episode_steps or self.default_max_steps,
            resolved=False,
            done=False,
            schema_drifted=False,
            done_reason="in_progress",
            cumulative_reward=0.0,
            current_logs=self._initial_logs(),
            valid_actions=list(self.valid_actions),
            history=[],
            last_action_error=None,
        )
        return self._build_observation(reward=0.0)

    def step(
        self,
        action: IncidentAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> IncidentObservation:
        if self._state.done:
            self._state.last_action_error = (
                "Episode already finished. Call reset() to start a new one."
            )
            return self._build_observation(reward=0.0, last_action=action.action)

        self._state.last_action_error = None
        self._state.step_count += 1

        if self._state.step_count == 3 and not self._state.resolved:
            self._state.current_logs = {
                "code": 504,
                "message": "gateway timeout",
                "service": "checkout-api",
                "trace_id": "inc-504-demo",
            }
            self._state.schema_drifted = True

        if action.action == "fix_bug" and (
            "error" in self._state.current_logs or "code" in self._state.current_logs
        ):
            self._state.resolved = True

        history_pairs = [
            (entry.step, entry.action)
            for entry in self._state.history
        ] + [(self._state.step_count, action.action)]

        reward = compute_reward(
            {
                "logs": self._state.current_logs,
                "step": self._state.step_count,
                "resolved": self._state.resolved,
            },
            action.action,
            history_pairs,
            self._state.step_count,
        )

        self._state.cumulative_reward = round(self._state.cumulative_reward + reward, 3)
        self._state.history.append(
            HistoryEntry(
                step=self._state.step_count,
                action=action.action,
                reward=reward,
                resolved_after_action=self._state.resolved,
            )
        )

        self._state.done = self._state.resolved or (
            self._state.step_count >= self._state.max_steps
        )
        if self._state.resolved:
            self._state.done_reason = "resolved"
        elif self._state.step_count >= self._state.max_steps:
            self._state.done_reason = "max_steps_reached"
        else:
            self._state.done_reason = "in_progress"

        return self._build_observation(reward=reward, last_action=action.action)

    @property
    def state(self) -> IncidentState:
        return self._state

    def get_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(
            name="Incident Response OpenEnv",
            description=(
                "Diagnose a timeout incident, notice the mid-episode schema drift, "
                "and resolve the outage efficiently."
            ),
            version="1.1.0",
            documentation_url="https://github.com/chirayugk/incident-response-openenv",
            author="chirayugk",
        )
