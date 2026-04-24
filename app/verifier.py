def check_success(state):
    return state["resolved"]

def check_schema_handling(state, history):
    # agent must act correctly after schema drift
    for step, action in history:
        if "code" in state["logs"] and action == "fix_bug":
            return True
    return False

def check_progress(action):
    return action == "check_logs"