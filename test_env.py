from __future__ import annotations

import time
from typing import Any, Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from pydantic import BaseModel

DEFAULT_BASE_URL = "https://arzunn-incident-response-openenv.hf.space"


class IncidentAction(BaseModel):
    agent: str
    action: str
    note: str = ""


class DynamicEnv(EnvClient[IncidentAction, Dict, Dict]):
    def _step_payload(self, action: IncidentAction) -> Dict:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: Dict) -> StepResult[Dict]:
        return StepResult(
            observation=payload.get("observation", {}),
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> Dict:
        return payload


def summarize(obs: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "step": obs.get("step"),
        "turn_agent": obs.get("turn_agent"),
        "resolved": obs.get("resolved"),
        "done": obs.get("done"),
        "team_rewards": obs.get("team_rewards", {}),
        "logs": obs.get("logs", {}),
        "metadata": obs.get("metadata", {}),
    }


def next_action_for_turn(obs: Dict[str, Any]) -> tuple[str, str]:
    turn = obs.get("turn_agent", "manager")
    if turn == "manager":
        if obs.get("incident_detected", False):
            return turn, "assign_bugfix"
        return turn, "triage_backlog"
    if turn == "monitor":
        if obs.get("patch_ready", False) and not obs.get("tests_green", False):
            return turn, "verify_fix"
        if obs.get("incident_detected", False):
            return turn, "alert_incident"
        return turn, "scan_logs"
    if not obs.get("assignment_ready", False):
        return turn, "report_blocker"
    if not obs.get("patch_ready", False):
        return turn, "implement_fix"
    if not obs.get("tests_green", False):
        return turn, "write_test"
    return turn, "claim_done"


def verify_transition(prev: Dict[str, Any], cur: Dict[str, Any]) -> None:
    prev_step = prev.get("step", -1)
    cur_step = cur.get("step", -1)
    if cur_step <= prev_step:
        raise RuntimeError(f"Invalid transition: step did not advance ({prev_step} -> {cur_step}).")


def run_validation(base_url: str = DEFAULT_BASE_URL, max_steps: int = 12, sleep_s: float = 0.0) -> None:
    with DynamicEnv(base_url=base_url).sync() as env:
        obs = env.reset().observation
        prev = summarize(obs)
        print("=== RESET ===")
        print(prev)
        for i in range(max_steps):
            agent, action = next_action_for_turn(obs)
            step_result = env.step(IncidentAction(agent=agent, action=action, note=f"validation_step_{i}"))
            obs = step_result.observation
            cur = summarize(obs)
            print(f"\n=== STEP {i + 1} ===")
            print("action:", {"agent": agent, "action": action})
            print("reward:", step_result.reward)
            print("state:", cur)
            if step_result.done:
                print("\nEpisode ended.")
                break
            verify_transition(prev, cur)
            prev = cur
            if sleep_s > 0:
                time.sleep(sleep_s)


if __name__ == "__main__":
    run_validation()
