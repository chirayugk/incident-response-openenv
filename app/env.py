from models import IncidentAction
from server.incident_response_environment import IncidentResponseEnvironment


class IncidentEnv:
    """Compatibility wrapper over the OpenEnv-native environment."""

    def __init__(self) -> None:
        self._env = IncidentResponseEnvironment()
        self.valid_actions = list(self._env.valid_actions)

    def reset(self, **kwargs):
        return self._env.reset(**kwargs)

    def step(self, action: str):
        observation = self._env.step(IncidentAction(action=action))
        return (
            observation,
            float(observation.reward or 0.0),
            observation.done,
            observation.metadata,
        )

    def snapshot(self):
        return self._env.state
