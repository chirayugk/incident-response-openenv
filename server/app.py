from __future__ import annotations

import os

import uvicorn
from openenv.core.env_server import create_app
from starlette.responses import HTMLResponse

try:
    from ..models import IncidentAction, IncidentObservation
    from .incident_response_environment import IncidentResponseEnvironment
except ImportError:
    from models import IncidentAction, IncidentObservation
    from server.incident_response_environment import IncidentResponseEnvironment


app = create_app(
    IncidentResponseEnvironment,
    IncidentAction,
    IncidentObservation,
    env_name="multi_agent_incident_response_openenv",
    max_concurrent_envs=4,
)


@app.get("/ops-center", include_in_schema=False)
def ops_center() -> HTMLResponse:
    return HTMLResponse(
        """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Ops Center - Multi-Agent OpenEnv</title>
    <style>
      :root {
        --bg: #0a0d18;
        --panel: #131a30;
        --panel-soft: #1a2342;
        --accent: #79b8ff;
        --ok: #73f2ba;
        --warn: #ffc37a;
        --danger: #ff808d;
        --text: #eef3ff;
        --muted: #acb9d9;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Inter, Segoe UI, sans-serif;
        background: radial-gradient(circle at top, #1b2250, var(--bg) 58%);
        color: var(--text);
      }
      .wrap { max-width: 1200px; margin: 24px auto; padding: 0 16px; }
      .hero, .panel {
        background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
        border: 1px solid rgba(172,185,217,0.2);
        border-radius: 16px;
      }
      .hero { padding: 18px 20px; }
      .title { font-size: 28px; font-weight: 700; margin: 0 0 8px; }
      .subtitle { color: var(--muted); margin: 0; }
      .top-row {
        margin-top: 14px;
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 14px;
      }
      .controls {
        display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px;
      }
      button {
        border: none;
        border-radius: 9px;
        padding: 10px 14px;
        background: #2c4f88;
        color: #fff;
        cursor: pointer;
        font-weight: 600;
      }
      button:hover { opacity: 0.92; }
      .ghost { background: #31405f; }
      .warn { background: #7a4f25; }
      .ok { background: #225b41; }
      .status-line { margin-top: 8px; color: var(--muted); font-size: 14px; }
      .pill {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 999px;
        margin-right: 8px;
        margin-top: 8px;
        font-size: 12px;
      }
      .pill-ok { background: rgba(115,242,186,0.15); color: var(--ok); }
      .pill-warn { background: rgba(255,195,122,0.15); color: var(--warn); }
      .metrics {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
      }
      .metric {
        background: var(--panel-soft);
        border-radius: 12px;
        padding: 12px;
      }
      .metric-label { color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
      .metric-value { font-size: 22px; font-weight: 700; margin-top: 6px; }
      .agents {
        margin-top: 14px;
        display: grid;
        grid-template-columns: repeat(3, minmax(220px, 1fr));
        gap: 12px;
      }
      .agent-card {
        background: var(--panel);
        border: 1px solid rgba(172,185,217,0.22);
        border-radius: 14px;
        padding: 14px;
      }
      .agent-card.active { border-color: var(--accent); box-shadow: 0 0 0 1px rgba(121,184,255,0.35) inset; }
      .role { color: var(--accent); font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }
      .big { margin-top: 8px; font-size: 18px; font-weight: 700; }
      .small { margin-top: 6px; color: var(--muted); font-size: 13px; line-height: 1.4; }
      .bottom {
        margin-top: 14px;
        display: grid;
        grid-template-columns: 1.3fr 1fr;
        gap: 12px;
      }
      .panel { padding: 14px; }
      .panel h3 { margin: 0 0 10px; font-size: 16px; }
      .timeline, .logs {
        max-height: 270px;
        overflow: auto;
        font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
        font-size: 12px;
        line-height: 1.4;
        white-space: pre-wrap;
      }
      .entry { margin: 0 0 7px; color: #d8e2ff; }
      .err { color: var(--danger); }
      .note { color: var(--muted); font-size: 12px; margin-top: 8px; }
      a { color: var(--accent); }
      @media (max-width: 930px) {
        .top-row, .bottom, .agents { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <div class="wrap">
      <section class="hero">
        <h1 class="title">Multi-Agent Incident Ops Center</h1>
        <p class="subtitle">
          Interactive simulation of manager, analyst/monitor, and responder/engineer coordination.
        </p>
        <div>
          <span class="pill pill-ok">Rewards in [0,1] per agent</span>
          <span class="pill pill-warn">Hallucination / cheating penalties</span>
        </div>
        <div class="controls">
          <button id="startBtn" class="ok">Start Simulation</button>
          <button id="nextBtn">Next Turn</button>
          <button id="autoBtn">Auto Play</button>
          <button id="resetBtn" class="ghost">Reset</button>
          <button id="injectBtn" class="warn">Inject Sample Error</button>
        </div>
        <div id="statusLine" class="status-line">Ready. Click "Start Simulation".</div>
      </section>

      <section class="top-row">
        <div class="panel metrics">
          <div class="metric"><div class="metric-label">Step</div><div class="metric-value" id="stepMetric">0</div></div>
          <div class="metric"><div class="metric-label">Turn Agent</div><div class="metric-value" id="turnMetric">manager</div></div>
          <div class="metric"><div class="metric-label">Resolved</div><div class="metric-value" id="resolvedMetric">no</div></div>
        </div>
        <div class="panel">
          <h3>Live Endpoint</h3>
          <div class="small">OpenEnv interactive API/UI: <a href="/web/">/web/</a></div>
          <div class="note">This board is a role-play simulation for demos and presentations.</div>
        </div>
      </section>

      <section class="agents">
        <article class="agent-card" id="card-manager">
          <div class="role">Manager</div>
          <div class="big" id="managerAction">Awaiting assignment</div>
          <div class="small">Actions: triage_backlog, assign_bugfix, assign_investigation, reprioritize</div>
          <div class="small">Reward: <span id="managerReward">0.000</span></div>
        </article>
        <article class="agent-card" id="card-monitor">
          <div class="role">Analyst / Monitor</div>
          <div class="big" id="monitorAction">Monitoring idle</div>
          <div class="small">Actions: scan_logs, alert_incident, verify_fix</div>
          <div class="small">Reward: <span id="monitorReward">0.000</span></div>
        </article>
        <article class="agent-card" id="card-engineer">
          <div class="role">Responder / Engineer</div>
          <div class="big" id="engineerAction">Waiting for ticket</div>
          <div class="small">Actions: inspect_code, implement_fix, write_test, claim_done</div>
          <div class="small">Reward: <span id="engineerReward">0.000</span></div>
        </article>
      </section>

      <section class="bottom">
        <article class="panel">
          <h3>Simulation Timeline</h3>
          <div id="timeline" class="timeline"></div>
        </article>
        <article class="panel">
          <h3>Error / DevOps Sample Logs</h3>
          <div id="logs" class="logs"></div>
        </article>
      </section>
    </div>

    <script>
      const state = {
        step: 0,
        maxSteps: 12,
        resolved: false,
        turnAgent: "manager",
        incidentDetected: false,
        assignmentReady: false,
        patchReady: false,
        testsGreen: false,
        teamRewards: { manager: 0, monitor: 0, engineer: 0 },
        playing: false,
        timer: null
      };

      const roleOrder = ["manager", "monitor", "engineer"];
      const actionTextEl = {
        manager: document.getElementById("managerAction"),
        monitor: document.getElementById("monitorAction"),
        engineer: document.getElementById("engineerAction"),
      };
      const rewardEl = {
        manager: document.getElementById("managerReward"),
        monitor: document.getElementById("monitorReward"),
        engineer: document.getElementById("engineerReward"),
      };

      const timelineEl = document.getElementById("timeline");
      const logsEl = document.getElementById("logs");
      const statusLine = document.getElementById("statusLine");
      const stepMetric = document.getElementById("stepMetric");
      const turnMetric = document.getElementById("turnMetric");
      const resolvedMetric = document.getElementById("resolvedMetric");

      function addTimeline(line, danger = false) {
        const p = document.createElement("div");
        p.className = "entry" + (danger ? " err" : "");
        p.textContent = line;
        timelineEl.prepend(p);
      }

      function addLog(line, danger = false) {
        const p = document.createElement("div");
        p.className = "entry" + (danger ? " err" : "");
        p.textContent = line;
        logsEl.prepend(p);
      }

      function setActiveCard(role) {
        ["manager", "monitor", "engineer"].forEach((r) => {
          const card = document.getElementById(`card-${r}`);
          card.classList.toggle("active", r === role);
        });
      }

      function updateView() {
        stepMetric.textContent = String(state.step);
        turnMetric.textContent = state.turnAgent;
        resolvedMetric.textContent = state.resolved ? "yes" : "no";
        statusLine.textContent = state.resolved
          ? "Incident resolved. Reset to replay."
          : `Turn: ${state.turnAgent} | step ${state.step}/${state.maxSteps}`;
        setActiveCard(state.turnAgent);
        rewardEl.manager.textContent = state.teamRewards.manager.toFixed(3);
        rewardEl.monitor.textContent = state.teamRewards.monitor.toFixed(3);
        rewardEl.engineer.textContent = state.teamRewards.engineer.toFixed(3);
      }

      function nextRole() {
        const idx = roleOrder.indexOf(state.turnAgent);
        return roleOrder[(idx + 1) % roleOrder.length];
      }

      function decideAction() {
        if (state.turnAgent === "manager") {
          if (!state.incidentDetected) return "triage_backlog";
          if (!state.assignmentReady) return "assign_bugfix";
          return "reprioritize";
        }
        if (state.turnAgent === "monitor") {
          if (!state.incidentDetected) return "scan_logs";
          if (state.patchReady && !state.testsGreen) return "verify_fix";
          return "alert_incident";
        }
        if (!state.assignmentReady) return "report_blocker";
        if (!state.patchReady) return "implement_fix";
        if (!state.testsGreen) return "write_test";
        return "claim_done";
      }

      function shapedReward(role, action) {
        let reward = 0.1;
        if (role === "manager" && action === "assign_bugfix") reward = 0.74;
        if (role === "manager" && action === "triage_backlog") reward = 0.45;
        if (role === "manager" && action === "reprioritize") reward = 0.63;
        if (role === "monitor" && action === "scan_logs") reward = 0.44;
        if (role === "monitor" && action === "alert_incident") reward = 0.79;
        if (role === "monitor" && action === "verify_fix") reward = 0.73;
        if (role === "engineer" && action === "report_blocker") reward = 0.09;
        if (role === "engineer" && action === "implement_fix") reward = 0.88;
        if (role === "engineer" && action === "write_test") reward = 0.79;
        if (role === "engineer" && action === "claim_done") reward = state.testsGreen ? 1.0 : 0.0;
        return Math.max(0, Math.min(1, reward));
      }

      function applyEffects(role, action) {
        if (state.step === 3) {
          addLog("[ERROR] schema_drift_detected: switched to code=504 payload", true);
        }
        if (role === "monitor" && action === "scan_logs") {
          state.incidentDetected = true;
          addLog("[monitor] anomaly_score=0.97 high_alert=true service=checkout-api");
        }
        if (role === "monitor" && action === "alert_incident") {
          addLog("[pager] incident_raised id=INC-504 severity=critical trace=inc-504-demo", true);
        }
        if (role === "manager" && action === "assign_bugfix") {
          state.assignmentReady = state.incidentDetected;
        }
        if (role === "engineer" && action === "implement_fix") {
          state.patchReady = true;
          addLog("[ci] build passed for hotfix branch feat/incident-504");
        }
        if (role === "monitor" && action === "verify_fix" && state.patchReady) {
          state.testsGreen = true;
          addLog("[devops] canary 5m error_rate=0.02% latency_p95=128ms");
        }
        if (role === "engineer" && action === "claim_done" && state.patchReady && state.testsGreen) {
          state.resolved = true;
          addLog("[ops] incident_status=resolved mttr=9 turns");
        }
      }

      function tick() {
        if (state.resolved || state.step >= state.maxSteps) {
          state.playing = false;
          clearInterval(state.timer);
          updateView();
          return;
        }
        state.step += 1;
        const role = state.turnAgent;
        const action = decideAction();
        actionTextEl[role].textContent = action;
        applyEffects(role, action);
        const reward = shapedReward(role, action);
        state.teamRewards[role] = Math.min(1, state.teamRewards[role] * 0.65 + reward * 0.35);
        addTimeline(`[step ${state.step}] ${role} -> ${action} | reward=${reward.toFixed(3)} | resolved=${state.resolved}`);
        if (!state.resolved) state.turnAgent = nextRole();
        updateView();
      }

      function reset() {
        state.step = 0;
        state.resolved = false;
        state.turnAgent = "manager";
        state.incidentDetected = false;
        state.assignmentReady = false;
        state.patchReady = false;
        state.testsGreen = false;
        state.teamRewards = { manager: 0, monitor: 0, engineer: 0 };
        state.playing = false;
        clearInterval(state.timer);
        timelineEl.innerHTML = "";
        logsEl.innerHTML = "";
        actionTextEl.manager.textContent = "Awaiting assignment";
        actionTextEl.monitor.textContent = "Monitoring idle";
        actionTextEl.engineer.textContent = "Waiting for ticket";
        addLog("[boot] ops-center initialized");
        addLog("[sample] timeout errors detected in checkout-api", true);
        updateView();
      }

      document.getElementById("startBtn").addEventListener("click", () => {
        if (state.step === 0) addTimeline("Simulation started.");
        tick();
      });
      document.getElementById("nextBtn").addEventListener("click", tick);
      document.getElementById("autoBtn").addEventListener("click", () => {
        if (state.playing) return;
        state.playing = true;
        state.timer = setInterval(() => {
          if (state.resolved || state.step >= state.maxSteps) {
            clearInterval(state.timer);
            state.playing = false;
            return;
          }
          tick();
        }, 900);
      });
      document.getElementById("resetBtn").addEventListener("click", reset);
      document.getElementById("injectBtn").addEventListener("click", () => {
        addLog("[sample-error] unknown_auth_header format mismatch from edge-gateway", true);
        addTimeline("Injected sample unknown/invalid header error for investigation.", true);
      });

      reset();
    </script>
  </body>
</html>
"""
    )


def main(host: str = "0.0.0.0", port: int | None = None) -> None:
    uvicorn.run(app, host=host, port=port or int(os.getenv("PORT", "7860")))


if __name__ == "__main__":
    main()
