from __future__ import annotations

from typing import Any, Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from pydantic import BaseModel

DEFAULT_BASE_URL = "https://arzunn-incident-response-openenv.hf.space"
ROLE_MAP = {"manager": "manager", "analyst": "monitor", "responder": "engineer"}


class IncidentAction(BaseModel):
    agent: str
    action: str
    note: str = ""


class DynamicEnv(EnvClient[IncidentAction, Dict, Dict]):
    def _step_payload(self, action: IncidentAction) -> Dict:
        return action.model_dump(exclude_none=True)

    def _parse_result(self, payload: Dict) -> StepResult[Dict]:
        return StepResult(observation=payload.get("observation", {}), reward=payload.get("reward"), done=payload.get("done", False))

    def _parse_state(self, payload: Dict) -> Dict:
        return payload


def pick_action_for_role(role: str, obs: Dict[str, Any]) -> str:
    if role == "manager":
        return "assign_bugfix" if obs.get("incident_detected", False) else "triage_backlog"
    if role == "analyst":
        if obs.get("patch_ready", False) and not obs.get("tests_green", False):
            return "verify_fix"
        return "scan_logs" if not obs.get("incident_detected", False) else "alert_incident"
    if not obs.get("assignment_ready", False):
        return "report_blocker"
    if not obs.get("patch_ready", False):
        return "implement_fix"
    if not obs.get("tests_green", False):
        return "write_test"
    return "claim_done"


def run_demo(base_url: str = DEFAULT_BASE_URL, max_cycles: int = 6) -> None:
    with DynamicEnv(base_url=base_url).sync() as env:
        obs = env.reset().observation
        roles = ["manager", "analyst", "responder"]
        total_reward = 0.0
        print("=== Multi-Agent Sequential Demo ===")
        print("start:", {"step": obs.get("step"), "turn_agent": obs.get("turn_agent")})
        for cycle in range(1, max_cycles + 1):
            print(f"\n--- cycle {cycle} ---")
            for role in roles:
                if obs.get("resolved", False):
                    break
                if obs.get("turn_agent") != ROLE_MAP[role]:
                    continue
                action = pick_action_for_role(role, obs)
                prev_step = obs.get("step")
                result = env.step(IncidentAction(agent=ROLE_MAP[role], action=action, note=f"demo:{role}"))
                obs = result.observation
                reward = float(result.reward or 0.0)
                total_reward += reward
                print(f"{role:9s} -> {action:18s} | step {prev_step} -> {obs.get('step')} | reward={reward:.3f} | resolved={obs.get('resolved')}")
            if obs.get("resolved", False):
                break
        print("\nfinal:")
        print({
            "done": obs.get("done"),
            "resolved": obs.get("resolved"),
            "steps": obs.get("step"),
            "team_rewards": obs.get("team_rewards", {}),
            "total_reward": round(total_reward, 3),
            "done_reason": obs.get("metadata", {}).get("done_reason"),
        })


if __name__ == "__main__":
    run_demo()
