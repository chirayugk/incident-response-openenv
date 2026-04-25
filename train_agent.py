from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from pydantic import BaseModel

from llm_agent import LLMAgent, llm_action_to_env

DEFAULT_BASE_URL = "https://arzunn-incident-response-openenv.hf.space"
DEFAULT_EPISODES = 10
DEFAULT_MAX_STEPS = 12
DEFAULT_FAILURE_LOG_PATH = "failed_episodes.json"


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
class Metrics:
    success_rate: float
    average_reward: float
    average_steps_to_resolution: float


def run_episode(env: DynamicEnv, agent: LLMAgent, max_steps: int) -> Dict[str, Any]:
    obs = env.reset().observation
    total_reward = 0.0
    step_count = 0
    transitions: List[Dict[str, Any]] = []
    for _ in range(max_steps):
        role = obs.get("turn_agent", "manager")
        decision = agent.choose_action(obs)
        env_action = llm_action_to_env(role, decision.action)
        step_result = env.step(IncidentAction(agent=role, action=env_action, note=f"llm:{decision.action}"))
        obs = step_result.observation
        reward = float(step_result.reward or 0.0)
        transitions.append({
            "state": obs,
            "action": {"role": role, "llm_action": decision.action, "env_action": env_action, "raw_model_output": decision.raw_response},
            "response": {"reward": reward, "done": step_result.done, "resolved": obs.get("resolved", False), "metadata": obs.get("metadata", {})},
        })
        total_reward += reward
        step_count += 1
        status = "resolved" if obs.get("resolved", False) else "in_progress"
        if status == "resolved" or step_result.done:
            break
    return {
        "resolved": bool(obs.get("resolved", False)),
        "steps": step_count,
        "total_reward": round(total_reward, 3),
        "transitions": transitions,
        "final_state": obs,
    }


def evaluate(episodes: List[Dict[str, Any]]) -> Metrics:
    if not episodes:
        return Metrics(0.0, 0.0, 0.0)
    successes = [e for e in episodes if e["resolved"]]
    success_rate = len(successes) / len(episodes)
    average_reward = sum(e["total_reward"] for e in episodes) / len(episodes)
    avg_steps = (sum(e["steps"] for e in successes) / len(successes)) if successes else 0.0
    return Metrics(round(success_rate, 3), round(average_reward, 3), round(avg_steps, 3))


def save_failed_episodes(episodes: List[Dict[str, Any]], path: str) -> None:
    failed = []
    for i, ep in enumerate(episodes, start=1):
        if ep["resolved"]:
            continue
        failed.append({"episode": i, "steps": ep["steps"], "total_reward": ep["total_reward"], "trace": ep["transitions"]})
    Path(path).write_text(json.dumps(failed, indent=2), encoding="utf-8")


def train(base_url: str = DEFAULT_BASE_URL, episodes: int = DEFAULT_EPISODES, max_steps: int = DEFAULT_MAX_STEPS, failure_log_path: str = DEFAULT_FAILURE_LOG_PATH) -> None:
    llm_agent = LLMAgent()
    episode_results: List[Dict[str, Any]] = []
    with DynamicEnv(base_url=base_url).sync() as env:
        for ep in range(1, episodes + 1):
            ep_result = run_episode(env, llm_agent, max_steps=max_steps)
            episode_results.append(ep_result)
            print(f"episode={ep} resolved={ep_result['resolved']} steps={ep_result['steps']} reward={ep_result['total_reward']:.3f}")
    metrics = evaluate(episode_results)
    save_failed_episodes(episode_results, failure_log_path)
    print("\n=== Evaluation Summary ===")
    print(f"success_rate: {metrics.success_rate}")
    print(f"average_reward: {metrics.average_reward}")
    print(f"average_steps_to_resolution: {metrics.average_steps_to_resolution}")
    print(f"failed_episodes_logged_to: {failure_log_path}")


if __name__ == "__main__":
    train()
