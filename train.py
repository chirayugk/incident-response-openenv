from app.env import IncidentEnv


env = IncidentEnv()

for episode in range(5):
    observation = env.reset()
    total_reward = 0.0

    print(f"\nEpisode {episode}")

    for _ in range(6):
        action = "fix_bug" if observation.step > 1 else "check_logs"
        observation, reward, done, info = env.step(action)

        print("Action:", action)
        print("State:", observation)
        print("Reward:", reward)
        print("Info:", info)

        total_reward += reward

        if done:
            break

    print("Total Reward:", round(total_reward, 3))
