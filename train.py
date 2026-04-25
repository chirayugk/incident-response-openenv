from __future__ import annotations

from agent import MultiAgentCoordinator
from models import IncidentAction
from server.incident_response_environment import IncidentResponseEnvironment


def run_episode(env: IncidentResponseEnvironment, coordinator: MultiAgentCoordinator) -> None:
    obs = env.reset()
    total_reward = 0.0

    print("\n=== New Multi-Agent Episode ===")
    while not obs.done:
        state = obs.model_dump()
        agent, action = coordinator.choose_action(state)
        obs = env.step(
            IncidentAction(
                agent=agent,
                action=action,
                note=f"{agent} executed {action}",
            )
        )
        reward = float(obs.reward or 0.0)
        total_reward += reward
        print(
            f"step={obs.step:02d} turn={state.get('turn_agent')} action={action:<20} "
            f"reward={reward:.3f} team_rewards={obs.team_rewards}"
        )

    print(f"done_reason={obs.metadata.get('done_reason')} total_reward={total_reward:.3f}")
    print(f"hallucinations={obs.metadata.get('hallucination_count')}")


def main() -> None:
    env = IncidentResponseEnvironment(default_max_steps=12)
    coordinator = MultiAgentCoordinator()
    for _ in range(3):
        run_episode(env, coordinator)


if __name__ == "__main__":
    main()
