from models import IncidentAction
from server.incident_response_environment import IncidentResponseEnvironment

env = IncidentResponseEnvironment()

for episode in range(3):
    state = env.reset()
    total_reward = 0

    print(f"\n=== Episode {episode} ===")

    for step in range(6):
        action = "check_logs" if step < 2 else "fix_bug"

        state = env.step(IncidentAction(action=action))
        reward = float(state.reward or 0.0)
        done = state.done
        info = state.metadata

        print(f"Step {step}")
        print("Action:", action)
        print("State:", state)
        print("Reward:", reward)

        total_reward += reward

        if done:
            break

    print("Total Reward:", total_reward)
