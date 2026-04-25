from __future__ import annotations

from typing import Any, Dict


State = Dict[str, Any]


class ManagerAgent:
    name = "ManagerAgent"

    def choose_action(self, state: State) -> str:
        if not state.get("incident_detected"):
            return "triage_backlog"
        if not state.get("assignment_ready"):
            return "assign_bugfix"
        return "reprioritize"


class MonitorAgent:
    name = "MonitorAgent"

    def choose_action(self, state: State) -> str:
        if not state.get("incident_detected"):
            return "scan_logs"
        if state.get("patch_ready") and not state.get("tests_green"):
            return "verify_fix"
        return "alert_incident"


class EngineerAgent:
    name = "EngineerAgent"

    def choose_action(self, state: State) -> str:
        if not state.get("assignment_ready"):
            return "report_blocker"
        if not state.get("patch_ready"):
            return "implement_fix"
        if not state.get("tests_green"):
            return "write_test"
        return "claim_done"


class MultiAgentCoordinator:
    """Simple policy orchestrator mapping turn_agent -> sub-agent choice."""

    def __init__(self) -> None:
        self.manager = ManagerAgent()
        self.monitor = MonitorAgent()
        self.engineer = EngineerAgent()

    def choose_action(self, state: State) -> tuple[str, str]:
        turn_agent = state.get("turn_agent", "manager")
        if turn_agent == "manager":
            return turn_agent, self.manager.choose_action(state)
        if turn_agent == "monitor":
            return turn_agent, self.monitor.choose_action(state)
        return turn_agent, self.engineer.choose_action(state)
