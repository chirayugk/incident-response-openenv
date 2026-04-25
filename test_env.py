from models import IncidentAction
from server.incident_response_environment import IncidentResponseEnvironment

env = IncidentResponseEnvironment()

for episode in range(3):
    state = env.reset()
    total_reward = 0.0

    print(f"\n=== Episode {episode} ===")

    for step in range(12):
        role = state.turn_agent
        if role == "manager":
            action = "assign_bugfix" if state.incident_detected else "triage_backlog"
        elif role == "monitor":
            action = "scan_logs" if not state.incident_detected else "alert_incident"
        else:
            if not state.assignment_ready:
                action = "report_blocker"
            elif not state.patch_ready:
                action = "implement_fix"
            elif not state.tests_green:
                action = "write_test"
            else:
                action = "claim_done"

        state = env.step(IncidentAction(agent=role, action=action))
        reward = float(state.reward or 0.0)
        done = state.done
        info = state.metadata

        print(f"Step {step}")
        print("Agent:", role)
        print("Action:", action)
        print("State:", state)
        print("Reward:", reward)
        print("Team Rewards:", state.team_rewards)

        total_reward += reward

        if done:
            break

    print("Total Reward:", round(total_reward, 3))
    print("Done Reason:", info.get("done_reason"))
