import asyncio
import random
from datetime import datetime
from typing import Optional
from copy import deepcopy

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

DEFAULT_LOGS = [
    {
        "id": 1,
        "title": "Database Connection Failure",
        "severity": "HIGH",
        "timestamp": "2026-04-25T10:00:00",
        "description": "Primary database failed to respond. Connection timeout after 30s.",
        "resolved": False,
    },
    {
        "id": 2,
        "title": "High CPU Usage",
        "severity": "MEDIUM",
        "timestamp": "2026-04-25T10:05:00",
        "description": "CPU usage spiked to 95% on node-3. Possible runaway process.",
        "resolved": False,
    },
    {
        "id": 3,
        "title": "Auth Service Error",
        "severity": "HIGH",
        "timestamp": "2026-04-25T10:10:00",
        "description": "Authentication service returned error 500. Brute-force attack suspected.",
        "resolved": False,
    },
    {
        "id": 4,
        "title": "Disk Space Warning",
        "severity": "LOW",
        "timestamp": "2026-04-25T10:15:00",
        "description": "Disk usage at 88% on storage-1. Cleanup recommended.",
        "resolved": False,
    },
    {
        "id": 5,
        "title": "Network Packet Loss",
        "severity": "MEDIUM",
        "timestamp": "2026-04-25T10:20:00",
        "description": "15% packet loss detected on edge router. Possible hardware failure.",
        "resolved": False,
    },
]

DEFAULT_AGENTS = {
    "manager": {
        "name": "Manager",
        "current_action": "idle",
        "message": "Waiting for incidents.",
        "status": "idle",
    },
    "monitor": {
        "name": "Monitor",
        "current_action": "idle",
        "message": "No anomalies detected.",
        "status": "idle",
    },
    "engineer": {
        "name": "Engineer",
        "current_action": "idle",
        "message": "Standing by.",
        "status": "idle",
    },
}

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

state = {
    "logs": deepcopy(DEFAULT_LOGS),
    "agents": deepcopy(DEFAULT_AGENTS),
    "reward_history": [],
    "system_status": "idle",
}

_running: bool = False
_lock = asyncio.Lock()

# ---------------------------------------------------------------------------
# Reward helpers
# ---------------------------------------------------------------------------

SEVERITY_REWARD = {"HIGH": 10, "MEDIUM": 5, "LOW": 2}
WRONG_ACTION_PENALTY = -3
DELAY_PENALTY = -1


def _compute_reward(action: str, log: Optional[dict]) -> int:
    if action == "resolve" and log and not log["resolved"]:
        return SEVERITY_REWARD.get(log["severity"], 0) + DELAY_PENALTY
    if action == "wrong":
        return WRONG_ACTION_PENALTY + DELAY_PENALTY
    return DELAY_PENALTY


# ---------------------------------------------------------------------------
# Agent logic helpers
# ---------------------------------------------------------------------------

ANOMALY_KEYWORDS = {"error", "failed", "attack", "failure", "spike", "loss"}


def _manager_act() -> dict:
    unresolved = [l for l in state["logs"] if not l["resolved"]]
    if not unresolved:
        return {
            "current_action": "monitor_queue",
            "message": "All incidents resolved. Monitoring queue.",
            "status": "done",
        }
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    top = sorted(unresolved, key=lambda l: severity_order.get(l["severity"], 9))[0]
    return {
        "current_action": f"prioritize:{top['id']}",
        "message": f"Prioritizing [{top['severity']}] '{top['title']}' (id={top['id']}).",
        "status": "working",
    }


def _monitor_act() -> dict:
    flagged = []
    for log in state["logs"]:
        if log["resolved"]:
            continue
        desc_words = set(log["description"].lower().split())
        title_words = set(log["title"].lower().split())
        if desc_words & ANOMALY_KEYWORDS or title_words & ANOMALY_KEYWORDS:
            flagged.append(log["id"])
    if flagged:
        return {
            "current_action": f"anomaly_detected:{flagged}",
            "message": f"Anomalies detected in log IDs: {flagged}.",
            "status": "working",
        }
    return {
        "current_action": "scanning",
        "message": "Scanning logs — no anomalies found.",
        "status": "idle",
    }


def _engineer_act() -> tuple[dict, int]:
    unresolved = [l for l in state["logs"] if not l["resolved"]]
    if not unresolved:
        return {
            "current_action": "standby",
            "message": "No open incidents. Standing by.",
            "status": "done",
        }, 0

    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    target = sorted(unresolved, key=lambda l: severity_order.get(l["severity"], 9))[0]

    # Resolve the log
    for log in state["logs"]:
        if log["id"] == target["id"]:
            log["resolved"] = True
            break

    reward = _compute_reward("resolve", target)
    return {
        "current_action": f"resolve:{target['id']}",
        "message": f"Resolved [{target['severity']}] '{target['title']}' (id={target['id']}). Reward: {reward}.",
        "status": "working",
    }, reward


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_state() -> dict:
    return {
        "logs": state["logs"],
        "agents": state["agents"],
        "reward_history": state["reward_history"],
        "system_status": state["system_status"],
    }


def reset_state():
    state["logs"] = deepcopy(DEFAULT_LOGS)
    state["agents"] = deepcopy(DEFAULT_AGENTS)
    state["reward_history"] = []
    state["system_status"] = "idle"
    global _running
    _running = False


def manual_step(agent: str, action: str, message: str) -> dict:
    if agent not in state["agents"]:
        raise ValueError(f"Unknown agent: {agent}")

    state["agents"][agent]["current_action"] = action
    state["agents"][agent]["message"] = message
    state["agents"][agent]["status"] = "working"
    state["system_status"] = "running"

    # Compute reward based on action keyword
    reward = DELAY_PENALTY
    if "resolve" in action.lower():
        unresolved_high = [l for l in state["logs"] if not l["resolved"] and l["severity"] == "HIGH"]
        unresolved_med = [l for l in state["logs"] if not l["resolved"] and l["severity"] == "MEDIUM"]
        unresolved_low = [l for l in state["logs"] if not l["resolved"] and l["severity"] == "LOW"]
        target = None
        if unresolved_high:
            target = unresolved_high[0]
        elif unresolved_med:
            target = unresolved_med[0]
        elif unresolved_low:
            target = unresolved_low[0]

        if target:
            target["resolved"] = True
            reward = _compute_reward("resolve", target)
        else:
            reward = WRONG_ACTION_PENALTY
    elif "wrong" in action.lower():
        reward = WRONG_ACTION_PENALTY + DELAY_PENALTY

    state["reward_history"].append(reward)

    all_resolved = all(l["resolved"] for l in state["logs"])
    state["system_status"] = "resolved" if all_resolved else "running"

    return {
        "agent": agent,
        "action": action,
        "message": message,
        "reward": reward,
        "system_status": state["system_status"],
    }


def is_running() -> bool:
    return _running


async def run_autonomous(steps: int = 10):
    global _running
    async with _lock:
        if _running:
            return {"detail": "Autonomous loop already running."}
        _running = True

    state["system_status"] = "running"

    try:
        for step in range(steps):
            if not _running:
                break

            # Manager
            m_update = _manager_act()
            state["agents"]["manager"].update(m_update)

            # Monitor
            mo_update = _monitor_act()
            state["agents"]["monitor"].update(mo_update)

            # Engineer
            e_update, reward = _engineer_act()
            state["agents"]["engineer"].update(e_update)
            state["reward_history"].append(reward)

            # Check resolved
            all_resolved = all(l["resolved"] for l in state["logs"])
            if all_resolved:
                state["system_status"] = "resolved"
                state["agents"]["manager"].update({"status": "done", "message": "All incidents resolved."})
                state["agents"]["monitor"].update({"status": "done", "message": "All clear."})
                state["agents"]["engineer"].update({"status": "done", "message": "All incidents resolved."})
                break

            await asyncio.sleep(random.uniform(1.0, 2.0))

        if state["system_status"] == "running":
            state["system_status"] = "idle"
    finally:
        _running = False


def stop_autonomous():
    global _running
    _running = False
    state["system_status"] = "idle"
