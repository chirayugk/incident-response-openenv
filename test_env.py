from app.env import IncidentEnv

env = IncidentEnv()

for episode in range(3):
    state = env.reset()
    total_reward = 0

    print(f"\n=== Episode {episode} ===")

    for step in range(6):
        if step < 2:
            action = "check_logs"
        else:
            action = "fix_bug"

        state, reward, done, info = env.step(action)

        print(f"Step {step}")
        print("Action:", action)
        print("State:", state)
        print("Reward:", reward)

        total_reward += reward

        if done:
            break

    print("Total Reward:", total_reward)