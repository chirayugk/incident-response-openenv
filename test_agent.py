from __future__ import annotations

from agent import MultiAgentCoordinator
from models import IncidentAction
from server.incident_response_environment import IncidentResponseEnvironment


def main() -> None:
    env = IncidentResponseEnvironment(default_max_steps=12)
    coordinator = MultiAgentCoordinator()
    obs = env.reset()

    while not obs.done:
        snapshot = obs.model_dump()
        role, action = coordinator.choose_action(snapshot)
        obs = env.step(
            IncidentAction(
                agent=role,
                action=action,
                note=f"policy:{role}:{action}",
            )
        )

    print("Episode finished.")
    print("done_reason:", obs.metadata.get("done_reason"))
    print("team_rewards:", obs.team_rewards)
    print("hallucination_count:", obs.metadata.get("hallucination_count"))


if __name__ == "__main__":
    main()
