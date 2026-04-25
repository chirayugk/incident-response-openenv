from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict

ALLOWED_LLM_ACTIONS = ["triage_backlog", "investigate_alert", "mitigate_threat", "ignore"]


@dataclass
class LLMDecision:
    action: str
    raw_response: str
    prompt: str


def state_to_prompt(state: Dict[str, Any]) -> str:
    return (
        "You are an incident response assistant.\n"
        "Choose exactly one action from: triage_backlog, investigate_alert, mitigate_threat, ignore.\n\n"
        f"State:\n{state}\n\n"
        "Return only the action token."
    )


def normalize_action(raw: str) -> str:
    token = (raw or "").strip().lower()
    return token if token in ALLOWED_LLM_ACTIONS else "ignore"


def default_model_infer(prompt: str) -> str:
    text = prompt.lower()
    # Fallback keyword model, used only if no structured inference is provided.
    if "resolved': true" in text or '"resolved": true' in text:
        return "ignore"
    if "assignment_ready': true" in text and "patch_ready': false" in text:
        return "mitigate_threat"
    if "incident_detected': false" in text:
        return "triage_backlog"
    if "incident_detected': true" in text:
        return "investigate_alert"
    return "ignore"


class LLMAgent:
    def __init__(self, model_infer: Callable[[str], str] | None = None) -> None:
        self.model_infer = model_infer or default_model_infer

    def choose_action(self, state: Dict[str, Any]) -> LLMDecision:
        prompt = state_to_prompt(state)
        role = state.get("turn_agent", "manager")

        # Primary policy: state-aware control logic to avoid loops.
        if role == "manager":
            if not state.get("incident_detected", False):
                raw = "triage_backlog"
            elif not state.get("assignment_ready", False):
                raw = "mitigate_threat"
            else:
                raw = "investigate_alert"
        elif role == "monitor":
            if not state.get("incident_detected", False):
                raw = "triage_backlog"
            elif state.get("patch_ready", False) and not state.get("tests_green", False):
                raw = "mitigate_threat"
            else:
                raw = "investigate_alert"
        else:  # engineer
            if not state.get("assignment_ready", False):
                raw = "ignore"
            elif not state.get("patch_ready", False):
                raw = "investigate_alert"
            elif not state.get("tests_green", False):
                raw = "triage_backlog"
            else:
                raw = "mitigate_threat"

        # Allow external model override if explicitly provided by caller.
        if self.model_infer is not default_model_infer:
            raw = self.model_infer(prompt)

        action = normalize_action(raw)
        return LLMDecision(action=action, raw_response=raw, prompt=prompt)


def llm_action_to_env(role: str, llm_action: str) -> str:
    mapping: Dict[str, Dict[str, str]] = {
        "manager": {
            "triage_backlog": "triage_backlog",
            "investigate_alert": "assign_investigation",
            "mitigate_threat": "assign_bugfix",
            "ignore": "idle",
        },
        "monitor": {
            "triage_backlog": "scan_logs",
            "investigate_alert": "alert_incident",
            "mitigate_threat": "verify_fix",
            "ignore": "idle",
        },
        "engineer": {
            "triage_backlog": "write_test",
            "investigate_alert": "implement_fix",
            "mitigate_threat": "claim_done",
            "ignore": "report_blocker",
        },
    }
    return mapping.get(role, {}).get(llm_action, "idle")
