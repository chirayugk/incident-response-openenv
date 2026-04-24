from models import IncidentAction
from server.incident_response_environment import IncidentResponseEnvironment


env = IncidentResponseEnvironment()

for episode in range(5):
    observation = env.reset()
    total_reward = 0.0

    print(f"\nEpisode {episode}")

    for _ in range(6):
        action_name = "fix_bug" if observation.step > 1 else "check_logs"
        observation = env.step(IncidentAction(action=action_name))
        reward = float(observation.reward or 0.0)
        done = observation.done
        info = observation.metadata

        print("Action:", action_name)
        print("State:", observation)
        print("Reward:", reward)
        print("Info:", info)

        total_reward += reward

        if done:
            break

    print("Total Reward:", round(total_reward, 3))
