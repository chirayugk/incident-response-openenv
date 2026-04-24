from app.verifier import check_success, check_schema_handling, check_progress

def compute_reward(state, action, history, step):
    reward = 0.0

    # ✅ 1. Success (most important)
    if check_success(state):
        reward += 0.6

    # 📈 2. Progress reward
    if check_progress(action):
        reward += 0.1

    # ⚡ 3. Efficiency reward (finish early)
    if state["resolved"]:
        efficiency_bonus = max(0, (6 - step) / 6) * 0.1
        reward += efficiency_bonus

    # 🚫 4. Penalties
    if action == "ignore":
        reward -= 0.1

    # ❗ Schema handling penalty
    if "code" in state["logs"] and action != "fix_bug":
        reward -= 0.2

    # 🚫 Anti-spam: repeating same action
    if len(history) >= 2:
        if history[-1][1] == history[-2][1]:
            reward -= 0.1

    # 🔒 Clamp to [0,1]
    reward = max(0.0, min(1.0, reward))

    return reward