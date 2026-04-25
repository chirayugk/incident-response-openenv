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



@app.get("/soc", include_in_schema=False)
def soc_dashboard() -> HTMLResponse:
    _APP_JSX = open(
        os.path.join(os.path.dirname(__file__), "..", "dashboard", "app.jsx"),
        encoding="utf-8",
    ).read() if os.path.isfile(
        os.path.join(os.path.dirname(__file__), "..", "dashboard", "app.jsx")
    ) else ""

    return HTMLResponse(
        f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Incident Response — SOC Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/babel-standalone@6/babel.min.js"></script>
  <script src="https://unpkg.com/recharts@2.12.7/umd/Recharts.js"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: 'Inter', sans-serif; background: #070b14; color: #e2e8f0; overflow-x: hidden; }}
    ::-webkit-scrollbar {{ width: 6px; }}
    ::-webkit-scrollbar-track {{ background: #0f172a; }}
    ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 3px; }}
    @keyframes pulse-dot {{ 0%,100%{{opacity:1;transform:scale(1)}} 50%{{opacity:.5;transform:scale(1.3)}} }}
    @keyframes slide-in {{ from{{opacity:0;transform:translateY(12px)}} to{{opacity:1;transform:translateY(0)}} }}
    @keyframes glow-red {{ 0%,100%{{box-shadow:0 0 8px #ef444433}} 50%{{box-shadow:0 0 20px #ef4444aa}} }}
    @keyframes fade-in {{ from{{opacity:0}} to{{opacity:1}} }}
    .pulse-dot {{ animation: pulse-dot 1.5s ease-in-out infinite; }}
    .slide-in {{ animation: slide-in 0.35s ease-out both; }}
    .glow-red {{ animation: glow-red 2s ease-in-out infinite; }}
    .fade-in {{ animation: fade-in 0.4s ease both; }}
    .glass {{ background: rgba(15,23,42,0.7); backdrop-filter: blur(12px); border: 1px solid rgba(148,163,184,0.08); }}
    .glass-bright {{ background: rgba(30,41,59,0.8); backdrop-filter: blur(16px); border: 1px solid rgba(148,163,184,0.12); }}
    .badge-high {{ background: rgba(239,68,68,0.15); color: #f87171; border: 1px solid rgba(239,68,68,0.3); }}
    .badge-medium {{ background: rgba(234,179,8,0.15); color: #facc15; border: 1px solid rgba(234,179,8,0.3); }}
    .badge-low {{ background: rgba(34,197,94,0.15); color: #4ade80; border: 1px solid rgba(34,197,94,0.3); }}
    .btn-primary {{ background: linear-gradient(135deg,#6366f1,#8b5cf6); transition: all .2s; }}
    .btn-primary:hover {{ transform: translateY(-1px); box-shadow: 0 8px 25px rgba(99,102,241,0.4); }}
    .btn-danger {{ background: linear-gradient(135deg,#ef4444,#dc2626); transition: all .2s; }}
    .btn-danger:hover {{ transform: translateY(-1px); box-shadow: 0 8px 25px rgba(239,68,68,0.4); }}
    .btn-green {{ background: linear-gradient(135deg,#22c55e,#16a34a); transition: all .2s; }}
    .btn-green:hover {{ transform: translateY(-1px); box-shadow: 0 8px 25px rgba(34,197,94,0.4); }}
    .btn-gray {{ background: rgba(51,65,85,0.8); border: 1px solid rgba(148,163,184,0.15); transition: all .2s; }}
    .btn-gray:hover {{ background: rgba(71,85,105,0.9); transform: translateY(-1px); }}
    .card-hover {{ transition: transform .2s, box-shadow .2s; }}
    .card-hover:hover {{ transform: translateY(-2px); box-shadow: 0 12px 40px rgba(0,0,0,0.4); }}
    input, select {{ background: rgba(15,23,42,0.8) !important; border: 1px solid rgba(148,163,184,0.2) !important; color: #e2e8f0 !important; outline: none !important; }}
    input:focus, select:focus {{ border-color: rgba(99,102,241,0.5) !important; box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important; }}
    select option {{ background: #1e293b; color: #e2e8f0; }}
    .grid-bg {{ background-image: radial-gradient(rgba(99,102,241,0.06) 1px, transparent 1px); background-size: 32px 32px; }}
  </style>
</head>
<body class="grid-bg min-h-screen">
  <div id="root"></div>
  <script type="text/babel">
{_APP_JSX}
  </script>
</body>
</html>"""
    )


def main(host: str = "0.0.0.0", port: int | None = None) -> None:
    uvicorn.run(app, host=host, port=port or int(os.getenv("PORT", "7860")))


if __name__ == "__main__":
    main()
