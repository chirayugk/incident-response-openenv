from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from pydantic import BaseModel

DEFAULT_BASE_URL = "https://arzunn-incident-response-openenv.hf.space"
DEFAULT_EPISODES = 5
DEFAULT_MAX_STEPS = 12

ROLE_ACTIONS = {
    "manager": ["triage_backlog", "assign_bugfix", "assign_investigation", "reprioritize", "idle"],
    "monitor": ["scan_logs", "alert_incident", "verify_fix", "idle"],
    "engineer": ["inspect_code", "implement_fix", "write_test", "report_blocker", "claim_done", "idle"],
}


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


@dataclass
class EpisodeResult:
    episode_id: int
    total_reward: float
    steps: int
    resolved: bool


def state_text(obs: Dict[str, Any]) -> str:
    logs = obs.get("logs", {})
    return " ".join(str(v).lower() for v in logs.values())


class RandomBaselineAgent:
    def __init__(self, seed: int = 7) -> None:
        self.rng = random.Random(seed)

    def choose_action(self, obs: Dict[str, Any]) -> Tuple[str, str]:
        role = obs.get("turn_agent", "manager")
        return role, self.rng.choice(ROLE_ACTIONS.get(role, ["idle"]))


class RuleBasedBaselineAgent:
    def choose_action(self, obs: Dict[str, Any]) -> Tuple[str, str]:
        role = obs.get("turn_agent", "manager")
        text = state_text(obs)
        high_alert = ("high_alert" in text) or ("critical" in text)
        unknown = "unknown" in text

        if role == "manager":
            if obs.get("incident_detected", False):
                return role, "assign_bugfix"
            return role, "triage_backlog"

        if role == "monitor":
            if high_alert or unknown:
                return role, "alert_incident"
            if not obs.get("incident_detected", False):
                return role, "scan_logs"
            return role, "verify_fix" if obs.get("patch_ready", False) else "alert_incident"

        if not obs.get("assignment_ready", False):
            return role, "report_blocker"
        if high_alert and not obs.get("patch_ready", False):
            return role, "implement_fix"
        if not obs.get("patch_ready", False):
            return role, "inspect_code"
        if not obs.get("tests_green", False):
            return role, "write_test"
        return role, "claim_done"


def run_episode(env: DynamicEnv, agent: Any, episode_id: int, max_steps: int) -> EpisodeResult:
    obs = env.reset().observation
    total_reward = 0.0
    steps = 0
    for _ in range(max_steps):
        role, action = agent.choose_action(obs)
        step_result = env.step(IncidentAction(agent=role, action=action, note=f"ep{episode_id}_{role}"))
        obs = step_result.observation
        total_reward += float(step_result.reward or 0.0)
        steps += 1
        if step_result.done:
            break
    return EpisodeResult(episode_id=episode_id, total_reward=round(total_reward, 3), steps=steps, resolved=bool(obs.get("resolved", False)))


def evaluate_agent(agent_name: str, agent: Any, base_url: str, episodes: int, max_steps: int) -> List[EpisodeResult]:
    results: List[EpisodeResult] = []
    with DynamicEnv(base_url=base_url).sync() as env:
        for ep in range(1, episodes + 1):
            result = run_episode(env, agent, ep, max_steps)
            results.append(result)
            print(f"[{agent_name}] episode={ep} reward={result.total_reward:.3f} steps={result.steps} resolved={result.resolved}")
    return results


if __name__ == "__main__":
    random_results = evaluate_agent("random", RandomBaselineAgent(seed=7), DEFAULT_BASE_URL, DEFAULT_EPISODES, DEFAULT_MAX_STEPS)
    rule_results = evaluate_agent("rule_based", RuleBasedBaselineAgent(), DEFAULT_BASE_URL, DEFAULT_EPISODES, DEFAULT_MAX_STEPS)
    print("\n=== Summary ===")
    print("random_total_rewards:", [r.total_reward for r in random_results])
    print("rule_total_rewards:", [r.total_reward for r in rule_results])
