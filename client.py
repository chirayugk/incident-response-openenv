from __future__ import annotations

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult

from .models import IncidentAction, IncidentObservation, IncidentState


class IncidentResponseEnv(
    EnvClient[IncidentAction, IncidentObservation, IncidentState]
):
    """Typed OpenEnv client for the Incident Response environment."""

    def _step_payload(self, action: IncidentAction) -> Dict:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: Dict) -> StepResult[IncidentObservation]:
        obs_data = payload.get("observation", {})
        observation = IncidentObservation.model_validate(
            {
                **obs_data,
                "done": payload.get("done", obs_data.get("done", False)),
                "reward": payload.get("reward", obs_data.get("reward")),
                "metadata": obs_data.get("metadata", {}),
            }
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> IncidentState:
        return IncidentState.model_validate(payload)
