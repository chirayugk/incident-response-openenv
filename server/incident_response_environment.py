from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import EnvironmentMetadata

try:
    from ..models import HistoryEntry, IncidentAction, IncidentObservation, IncidentState
except ImportError:
    from models import HistoryEntry, IncidentAction, IncidentObservation, IncidentState


class IncidentResponseEnvironment(
    Environment[IncidentAction, IncidentObservation, IncidentState]
):
    """OpenEnv-compatible multi-agent incident response simulator."""

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self, default_max_steps: int = 12):
        super().__init__()
        self.default_max_steps = default_max_steps
        self.turn_order = ["manager", "monitor", "engineer"]
        self.valid_actions = {
            "manager": [
                "triage_backlog",
                "assign_bugfix",
                "assign_investigation",
                "reprioritize",
                "idle",
            ],
            "monitor": ["scan_logs", "alert_incident", "verify_fix", "idle"],
            "engineer": [
                "inspect_code",
                "implement_fix",
                "write_test",
                "report_blocker",
                "claim_done",
                "idle",
            ],
        }
        self.default_task_id = "multi_agent_incident_response"
        self._state = IncidentState(
            episode_id=str(uuid4()),
            step_count=0,
            task_id=self.default_task_id,
            seed=None,
            max_steps=default_max_steps,
            resolved=False,
            done=False,
            incident_detected=False,
            assignment_ready=False,
            patch_ready=False,
            tests_green=False,
            schema_drifted=False,
            done_reason="not_started",
            cumulative_reward=0.0,
            current_logs={},
            valid_actions={k: list(v) for k, v in self.valid_actions.items()},
            turn_agent="manager",
            team_rewards={"manager": 0.0, "engineer": 0.0, "monitor": 0.0},
            hallucination_count=0,
            history=[],
            last_action_error=None,
        )
        self.reset()

    def _initial_logs(self) -> Dict[str, Any]:
        return {
            "error": "timeout",
            "service": "checkout-api",
            "region": "ap-south-1",
            "severity": "critical",
        }

    def _next_agent(self, current: str) -> str:
        idx = self.turn_order.index(current)
        return self.turn_order[(idx + 1) % len(self.turn_order)]

    def _acting_reward(self, action: IncidentAction) -> float:
        """Reward scale in [0,1], per role and state transition quality."""
        agent = action.agent
        name = action.action
        reward = 0.05
        hallucination = False

        if agent == "manager":
            if name == "triage_backlog":
                reward = 0.45
            elif name in ("assign_bugfix", "assign_investigation"):
                reward = 0.7 if self._state.incident_detected else 0.08
                if not self._state.incident_detected:
                    hallucination = True
            elif name == "reprioritize":
                reward = 0.55 if self._state.incident_detected else 0.2

        elif agent == "monitor":
            if name == "scan_logs":
                reward = 0.4
                if self._state.step_count >= 2:
                    self._state.incident_detected = True
            elif name == "alert_incident":
                reward = 0.75 if self._state.incident_detected else 0.05
                if not self._state.incident_detected:
                    hallucination = True
            elif name == "verify_fix":
                reward = 0.65 if self._state.patch_ready else 0.1
                if self._state.patch_ready:
                    self._state.tests_green = True

        elif agent == "engineer":
            if name == "inspect_code":
                reward = 0.45 if self._state.assignment_ready else 0.12
                if not self._state.assignment_ready:
                    hallucination = True
            elif name == "implement_fix":
                reward = 0.8 if self._state.assignment_ready else 0.1
                if self._state.assignment_ready:
                    self._state.patch_ready = True
            elif name == "write_test":
                reward = 0.7 if self._state.patch_ready else 0.15
                if self._state.patch_ready:
                    self._state.tests_green = True
            elif name == "claim_done":
                if self._state.patch_ready and self._state.tests_green:
                    reward = 0.95
                    self._state.resolved = True
                else:
                    reward = 0.0
                    hallucination = True

        if name == "idle":
            reward = 0.02

        if hallucination:
            self._state.hallucination_count += 1
            reward = max(0.0, reward - 0.45)
        return max(0.0, min(1.0, reward))

    def _team_bonus(self) -> float:
        if self._state.resolved:
            return 0.15
        if self._state.patch_ready and self._state.incident_detected:
            return 0.08
        if self._state.incident_detected:
            return 0.04
        return 0.0

    def _build_observation(
        self,
        reward: Optional[float],
        last_action: Optional[str] = None,
    ) -> IncidentObservation:
        return IncidentObservation(
            task_id=self._state.task_id,
            logs=self._state.current_logs,
            turn_agent=self._state.turn_agent,
            step=self._state.step_count,
            max_steps=self._state.max_steps,
            remaining_steps=max(self._state.max_steps - self._state.step_count, 0),
            incident_detected=self._state.incident_detected,
            assignment_ready=self._state.assignment_ready,
            patch_ready=self._state.patch_ready,
            tests_green=self._state.tests_green,
            resolved=self._state.resolved,
            schema_drifted=self._state.schema_drifted,
            valid_actions=list(self.valid_actions[self._state.turn_agent]),
            team_rewards=dict(self._state.team_rewards),
            last_action=last_action,
            history_length=len(self._state.history),
            done=self._state.done,
            reward=reward,
            metadata={
                "episode_id": self._state.episode_id,
                "done_reason": self._state.done_reason,
                "last_action_error": self._state.last_action_error,
                "hallucination_count": self._state.hallucination_count,
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
            incident_detected=False,
            assignment_ready=False,
            patch_ready=False,
            tests_green=False,
            schema_drifted=False,
            done_reason="in_progress",
            cumulative_reward=0.0,
            current_logs=self._initial_logs(),
            valid_actions={k: list(v) for k, v in self.valid_actions.items()},
            turn_agent="manager",
            team_rewards={"manager": 0.0, "engineer": 0.0, "monitor": 0.0},
            hallucination_count=0,
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

        if action.agent != self._state.turn_agent:
            self._state.last_action_error = (
                f"It is {self._state.turn_agent}'s turn, but received action from {action.agent}."
            )
            self._state.hallucination_count += 1
            acting_reward = 0.0
            team_bonus = 0.0
        else:
            if action.action not in self.valid_actions[action.agent]:
                self._state.last_action_error = (
                    f"Invalid action '{action.action}' for role '{action.agent}'."
                )
                self._state.hallucination_count += 1
                acting_reward = 0.0
                team_bonus = 0.0
            else:
                if action.agent == "manager" and action.action in (
                    "assign_bugfix",
                    "assign_investigation",
                ):
                    self._state.assignment_ready = self._state.incident_detected

                if self._state.step_count == 4 and not self._state.resolved:
                    self._state.current_logs = {
                        "code": 504,
                        "message": "gateway timeout",
                        "service": "checkout-api",
                        "trace_id": "inc-504-demo",
                        "severity": "critical",
                    }
                    self._state.schema_drifted = True

                acting_reward = self._acting_reward(action)
                team_bonus = self._team_bonus()

        reward = max(0.0, min(1.0, acting_reward + team_bonus))
        self._state.team_rewards[action.agent] = round(
            min(1.0, self._state.team_rewards[action.agent] * 0.65 + reward * 0.35), 3
        )

        self._state.cumulative_reward = round(self._state.cumulative_reward + reward, 3)
        self._state.history.append(
            HistoryEntry(
                step=self._state.step_count,
                agent=action.agent,
                action=action.action,
                reward=reward,
                cheating_or_hallucination=self._state.last_action_error is not None,
                note=action.note,
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
            self._state.turn_agent = self._next_agent(self._state.turn_agent)

        return self._build_observation(reward=reward, last_action=action.action)

    @property
    def state(self) -> IncidentState:
        return self._state

    def get_metadata(self) -> EnvironmentMetadata:
        return EnvironmentMetadata(
            name="Incident Response OpenEnv",
            description=(
                "Multi-agent incident response with Manager, Monitor, and Engineer "
                "coordination under schema drift, with anti-hallucination penalties."
            ),
            version="2.0.0",
            documentation_url="https://github.com/chirayugk/incident-response-openenv",
            author="chirayugk",
        )
