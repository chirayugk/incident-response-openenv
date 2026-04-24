from __future__ import annotations

import os
from typing import Any, Dict, Optional

import uvicorn
from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.env import IncidentEnv
from app.models import (
    Action,
    MetadataResponse,
    Observation,
    ResetRequest,
    ResetResponse,
    SchemaResponse,
    StateResponse,
    StepInfo,
    StepResult,
    TasksResponse,
)


APP_VERSION = "1.0.0"
BENCHMARK = "incident_response_openenv"

app = FastAPI(
    title="Incident Response - OpenEnv",
    version=APP_VERSION,
    description=(
        "A compact simulation where an agent diagnoses an outage, adapts to schema drift, "
        "and resolves the incident before the episode runs out of steps."
    ),
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = IncidentEnv()


UI_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Incident Response OpenEnv</title>
  <style>
    :root {
      --bg: #f5efe6;
      --panel: rgba(255, 251, 245, 0.94);
      --panel-strong: #ffffff;
      --ink: #1f2937;
      --muted: #667085;
      --line: #e7d8c6;
      --accent: #b54708;
      --accent-soft: #fff1e8;
      --success: #0f766e;
      --warn: #b42318;
      --info: #155eef;
      --shadow: 0 18px 40px rgba(31, 41, 55, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", "Trebuchet MS", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(181, 71, 8, 0.14), transparent 26%),
        radial-gradient(circle at top right, rgba(21, 94, 239, 0.10), transparent 24%),
        linear-gradient(180deg, #fdf8f2 0%, var(--bg) 100%);
    }

    .shell {
      max-width: 1400px;
      margin: 0 auto;
      padding: 28px 18px 40px;
    }

    .hero {
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: flex-start;
      margin-bottom: 20px;
    }

    .hero h1 {
      margin: 0 0 8px;
      font-size: clamp(28px, 3vw, 42px);
      line-height: 1.02;
    }

    .hero p {
      margin: 0;
      max-width: 760px;
      color: var(--muted);
      font-size: 15px;
    }

    .badge {
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid rgba(181, 71, 8, 0.16);
      background: var(--accent-soft);
      color: var(--accent);
      font-size: 13px;
      font-weight: 700;
      white-space: nowrap;
    }

    .grid {
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
    }

    .panel {
      background: var(--panel);
      backdrop-filter: blur(8px);
      border: 1px solid var(--line);
      border-radius: 24px;
      overflow: hidden;
      box-shadow: var(--shadow);
    }

    .panel-header {
      padding: 18px 20px 10px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
    }

    .panel-header h2 {
      margin: 0;
      font-size: 21px;
    }

    .panel-body {
      padding: 0 20px 20px;
    }

    .stats {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }

    .stat {
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--panel-strong);
      padding: 14px;
    }

    .stat-label {
      display: block;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 6px;
    }

    .stat-value {
      font-size: 24px;
      font-weight: 700;
    }

    .controls {
      display: grid;
      grid-template-columns: 1fr 0.8fr 0.8fr auto auto;
      gap: 12px;
      margin-bottom: 16px;
    }

    label {
      display: block;
      margin-bottom: 6px;
      font-size: 13px;
      font-weight: 700;
    }

    select, input, button {
      width: 100%;
      border-radius: 14px;
      border: 1px solid #d7cab9;
      font: inherit;
    }

    select, input {
      padding: 12px 13px;
      background: white;
      color: var(--ink);
    }

    button {
      padding: 12px 14px;
      font-weight: 700;
      cursor: pointer;
      background: var(--accent);
      color: white;
      transition: transform 0.14s ease, opacity 0.14s ease;
      align-self: end;
    }

    button:hover { transform: translateY(-1px); }
    button.secondary { background: #415a77; }
    button.ghost {
      background: white;
      color: var(--ink);
    }
    button:disabled {
      opacity: 0.55;
      cursor: wait;
      transform: none;
    }

    .action-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }

    .action-grid button {
      min-height: 88px;
      text-align: left;
      padding: 16px;
      border-radius: 18px;
    }

    .action-grid strong {
      display: block;
      margin-bottom: 6px;
      font-size: 16px;
    }

    .message {
      min-height: 48px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--panel-strong);
      padding: 14px 15px;
      margin-bottom: 16px;
      font-size: 14px;
    }

    .message.info { border-color: rgba(21, 94, 239, 0.22); color: var(--info); }
    .message.success { border-color: rgba(15, 118, 110, 0.24); color: var(--success); }
    .message.warn { border-color: rgba(180, 35, 24, 0.24); color: var(--warn); }

    .card {
      background: var(--panel-strong);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      margin-bottom: 16px;
    }

    .card h3 {
      margin: 0 0 10px;
      font-size: 16px;
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      word-break: break-word;
      font-family: "Consolas", "Courier New", monospace;
      font-size: 13px;
      line-height: 1.55;
      color: #243b53;
    }

    .history-list {
      display: grid;
      gap: 10px;
    }

    .history-item {
      display: grid;
      grid-template-columns: auto 1fr auto;
      gap: 12px;
      align-items: center;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--panel-strong);
      padding: 14px;
    }

    .history-step {
      width: 38px;
      height: 38px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 800;
    }

    .history-meta strong {
      display: block;
      margin-bottom: 2px;
    }

    .history-meta span,
    .history-score {
      color: var(--muted);
      font-size: 13px;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      background: #fff;
      border: 1px solid var(--line);
    }

    .status-pill.success {
      color: var(--success);
      border-color: rgba(15, 118, 110, 0.24);
    }

    .status-pill.warn {
      color: var(--warn);
      border-color: rgba(180, 35, 24, 0.24);
    }

    .status-pill.info {
      color: var(--info);
      border-color: rgba(21, 94, 239, 0.24);
    }

    @media (max-width: 1100px) {
      .grid { grid-template-columns: 1fr; }
      .controls { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }

    @media (max-width: 760px) {
      .hero { flex-direction: column; }
      .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .controls { grid-template-columns: 1fr; }
      .action-grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div>
        <h1 id="heroTitle">Incident Response OpenEnv</h1>
        <p id="heroDescription">Loading environment metadata...</p>
      </div>
      <div class="badge" id="heroBadge">booting</div>
    </section>

    <section class="grid">
      <article class="panel">
        <div class="panel-header">
          <h2>Control Room</h2>
          <div class="status-pill info" id="statusPill">Waiting for reset</div>
        </div>
        <div class="panel-body">
          <div class="stats">
            <div class="stat">
              <span class="stat-label">Step</span>
              <div class="stat-value" id="statStep">0</div>
            </div>
            <div class="stat">
              <span class="stat-label">Remaining</span>
              <div class="stat-value" id="statRemaining">0</div>
            </div>
            <div class="stat">
              <span class="stat-label">Reward</span>
              <div class="stat-value" id="statReward">0.00</div>
            </div>
            <div class="stat">
              <span class="stat-label">Resolved</span>
              <div class="stat-value" id="statResolved">No</div>
            </div>
          </div>

          <div class="controls">
            <div>
              <label for="taskSelect">Task</label>
              <select id="taskSelect"></select>
            </div>
            <div>
              <label for="seedInput">Seed</label>
              <input id="seedInput" type="number" min="0" value="7" />
            </div>
            <div>
              <label for="maxStepsInput">Max Steps</label>
              <input id="maxStepsInput" type="number" min="1" value="6" />
            </div>
            <button id="resetBtn" type="button">Reset</button>
            <button class="ghost" id="refreshBtn" type="button">Refresh</button>
          </div>

          <div class="action-grid">
            <button type="button" data-action="check_logs">
              <strong>Check Logs</strong>
              Inspect the current payload and gather progress reward.
            </button>
            <button type="button" data-action="fix_bug">
              <strong>Fix Bug</strong>
              Resolve the incident once you have enough evidence.
            </button>
            <button class="secondary" type="button" data-action="ignore">
              <strong>Ignore</strong>
              Skip action and take the penalty.
            </button>
          </div>

          <div class="message info" id="messageBox">Use Reset to start a fresh episode.</div>

          <div class="card">
            <h3>Current Observation</h3>
            <pre id="observationJson">{}</pre>
          </div>

          <div class="card">
            <h3>Log Payload</h3>
            <pre id="logsJson">{}</pre>
          </div>
        </div>
      </article>

      <article class="panel">
        <div class="panel-header">
          <h2>Episode State</h2>
          <div class="badge" id="historyBadge">0 actions</div>
        </div>
        <div class="panel-body">
          <div class="card">
            <h3>State Snapshot</h3>
            <pre id="stateJson">{}</pre>
          </div>

          <div class="card">
            <h3>Action History</h3>
            <div class="history-list" id="historyList">
              <div class="history-item">
                <div class="history-step">0</div>
                <div class="history-meta">
                  <strong>No actions yet</strong>
                  <span>Reset the environment to begin the drill.</span>
                </div>
                <div class="history-score">0.00</div>
              </div>
            </div>
          </div>
        </div>
      </article>
    </section>
  </div>

  <script>
    const els = {
      heroTitle: document.getElementById("heroTitle"),
      heroDescription: document.getElementById("heroDescription"),
      heroBadge: document.getElementById("heroBadge"),
      taskSelect: document.getElementById("taskSelect"),
      seedInput: document.getElementById("seedInput"),
      maxStepsInput: document.getElementById("maxStepsInput"),
      resetBtn: document.getElementById("resetBtn"),
      refreshBtn: document.getElementById("refreshBtn"),
      statStep: document.getElementById("statStep"),
      statRemaining: document.getElementById("statRemaining"),
      statReward: document.getElementById("statReward"),
      statResolved: document.getElementById("statResolved"),
      statusPill: document.getElementById("statusPill"),
      messageBox: document.getElementById("messageBox"),
      observationJson: document.getElementById("observationJson"),
      logsJson: document.getElementById("logsJson"),
      stateJson: document.getElementById("stateJson"),
      historyList: document.getElementById("historyList"),
      historyBadge: document.getElementById("historyBadge")
    };

    function pretty(value) {
      return JSON.stringify(value, null, 2);
    }

    function setBusy(isBusy) {
      els.resetBtn.disabled = isBusy;
      els.refreshBtn.disabled = isBusy;
      document.querySelectorAll("[data-action]").forEach((button) => {
        button.disabled = isBusy;
      });
    }

    function setMessage(text, tone = "info") {
      els.messageBox.textContent = text;
      els.messageBox.className = "message " + tone;
    }

    function setStatus(text, tone = "info") {
      els.statusPill.textContent = text;
      els.statusPill.className = "status-pill " + tone;
    }

    async function requestJSON(url, options = {}) {
      const response = await fetch(url, {
        ...options,
        headers: {
          "Content-Type": "application/json",
          ...(options.headers || {})
        }
      });

      const text = await response.text();
      const data = text ? JSON.parse(text) : {};

      if (!response.ok) {
        const detail = data.detail
          ? typeof data.detail === "string"
            ? data.detail
            : JSON.stringify(data.detail)
          : response.statusText;
        throw new Error(detail);
      }

      return data;
    }

    function renderObservation(observation, reward = 0) {
      els.statStep.textContent = String(observation.step);
      els.statRemaining.textContent = String(observation.remaining_steps);
      els.statReward.textContent = Number(reward).toFixed(2);
      els.statResolved.textContent = observation.resolved ? "Yes" : "No";
      els.observationJson.textContent = pretty(observation);
      els.logsJson.textContent = pretty(observation.logs);

      if (observation.resolved) {
        setStatus("Incident resolved", "success");
      } else if (observation.schema_drifted) {
        setStatus("Schema drift active", "warn");
      } else {
        setStatus("Monitoring incident", "info");
      }
    }

    function renderState(snapshot) {
      els.stateJson.textContent = pretty(snapshot);
      els.historyBadge.textContent = snapshot.history.length + " actions";

      if (!snapshot.history.length) {
        els.historyList.innerHTML = `
          <div class="history-item">
            <div class="history-step">0</div>
            <div class="history-meta">
              <strong>No actions yet</strong>
              <span>Reset the environment to begin the drill.</span>
            </div>
            <div class="history-score">0.00</div>
          </div>
        `;
        return;
      }

      els.historyList.innerHTML = snapshot.history.map((entry) => `
        <div class="history-item">
          <div class="history-step">${entry.step}</div>
          <div class="history-meta">
            <strong>${entry.action}</strong>
            <span>${entry.resolved_after_action ? "resolved after action" : "incident still open"}</span>
          </div>
          <div class="history-score">${Number(entry.reward).toFixed(2)}</div>
        </div>
      `).join("");
    }

    async function refreshState() {
      const data = await requestJSON("/state");
      renderState(data.state);
    }

    async function resetEnvironment() {
      const payload = {
        task_id: els.taskSelect.value,
        seed: Number(els.seedInput.value) || 7
      };

      const requestedMaxSteps = Number(els.maxStepsInput.value);
      if (requestedMaxSteps > 0) {
        payload.max_episode_steps = requestedMaxSteps;
      }

      const data = await requestJSON("/reset", {
        method: "POST",
        body: JSON.stringify(payload)
      });

      renderObservation(data.observation, 0);
      await refreshState();
      setMessage(
        `Episode reset for ${data.info.task_id} with seed ${data.info.seed}.`,
        "info"
      );
    }

    async function submitAction(action) {
      const data = await requestJSON("/step", {
        method: "POST",
        body: JSON.stringify({ action })
      });

      renderObservation(data.observation, data.reward);
      await refreshState();

      if (data.done && data.info.resolved) {
        setMessage(
          `Resolved in ${data.info.step} steps with reward ${Number(data.reward).toFixed(2)}.`,
          "success"
        );
      } else if (data.done) {
        setMessage(
          `Episode finished: ${data.info.done_reason}.`,
          "warn"
        );
      } else if (data.info.schema_drifted) {
        setMessage("The log schema has drifted. Watch the payload shape before acting.", "warn");
      } else {
        setMessage(`Action accepted: ${action}.`, "info");
      }
    }

    function populateTasks(tasks) {
      els.taskSelect.innerHTML = tasks.map((task) => `
        <option value="${task.task_id}">
          ${task.title} (${task.difficulty})
        </option>
      `).join("");

      if (tasks.length) {
        els.maxStepsInput.value = tasks[0].max_steps;
      }
    }

    async function init() {
      setBusy(true);
      try {
        const metadata = await requestJSON("/metadata");
        els.heroTitle.textContent = metadata.name;
        els.heroDescription.textContent = metadata.description;
        els.heroBadge.textContent = metadata.benchmark;
        populateTasks(metadata.tasks);
        await resetEnvironment();
      } catch (error) {
        setMessage(error.message, "warn");
      } finally {
        setBusy(false);
      }
    }

    els.resetBtn.addEventListener("click", async () => {
      setBusy(true);
      try {
        await resetEnvironment();
      } catch (error) {
        setMessage(error.message, "warn");
      } finally {
        setBusy(false);
      }
    });

    els.refreshBtn.addEventListener("click", async () => {
      setBusy(true);
      try {
        await refreshState();
        setMessage("State refreshed from the running environment.", "info");
      } catch (error) {
        setMessage(error.message, "warn");
      } finally {
        setBusy(false);
      }
    });

    document.querySelectorAll("[data-action]").forEach((button) => {
      button.addEventListener("click", async () => {
        setBusy(true);
        try {
          await submitAction(button.dataset.action);
        } catch (error) {
          setMessage(error.message, "warn");
        } finally {
          setBusy(false);
        }
      });
    });

    init();
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse, tags=["ui"])
def index() -> HTMLResponse:
    return HTMLResponse(UI_HTML)


@app.get("/health", tags=["system"])
def health() -> Dict[str, str]:
    return {"status": "healthy"}


@app.get("/metadata", response_model=MetadataResponse, tags=["system"])
def metadata() -> MetadataResponse:
    return MetadataResponse(
        name="Incident Response - OpenEnv",
        description=(
            "Diagnose a timeout incident, adapt when the log payload changes shape, "
            "and resolve the outage before the step budget runs out."
        ),
        benchmark=BENCHMARK,
        version=APP_VERSION,
        rewards_range=[0.0, 1.0],
        tasks=[env.task.model_copy(update={"max_steps": env.max_steps})],
    )


@app.get("/schema", response_model=SchemaResponse, tags=["system"])
def schema() -> SchemaResponse:
    return SchemaResponse(
        action=Action.model_json_schema(),
        observation=Observation.model_json_schema(),
        state=StateResponse.model_json_schema(),
    )


@app.get("/tasks", response_model=TasksResponse, tags=["openenv"])
def tasks() -> TasksResponse:
    return TasksResponse(tasks=[env.task.model_copy(update={"max_steps": env.max_steps})])


@app.get("/reset", response_model=ResetResponse, tags=["openenv"])
def reset_get() -> ResetResponse:
    observation = env.reset()
    return ResetResponse(
        observation=observation,
        info={
            "task_id": env.task.task_id,
            "seed": env.seed,
            "max_steps": observation.max_steps,
            "valid_actions": list(env.valid_actions),
        },
    )


@app.post("/reset", response_model=ResetResponse, tags=["openenv"])
def reset(req: Optional[ResetRequest] = Body(default=None)) -> ResetResponse:
    req = req or ResetRequest()
    try:
        observation = env.reset(
            task_id=req.task_id,
            seed=req.seed,
            max_episode_steps=req.max_episode_steps,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ResetResponse(
        observation=observation,
        info={
            "task_id": req.task_id,
            "seed": req.seed,
            "max_steps": observation.max_steps,
            "valid_actions": list(env.valid_actions),
        },
    )


@app.post("/step", response_model=StepResult, tags=["openenv"])
def step(action_payload: Dict[str, Any]) -> StepResult:
    try:
        action = Action.model_validate(action_payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    observation, reward, done, info = env.step(action.action)
    return StepResult(
        observation=observation,
        reward=reward,
        done=done,
        info=StepInfo.model_validate(info),
    )


@app.get("/state", response_model=StateResponse, tags=["openenv"])
def state() -> StateResponse:
    return StateResponse(state=env.snapshot())


@app.post("/mcp", tags=["system"])
def mcp(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": payload.get("id"),
        "error": {
            "code": -32601,
            "message": "MCP tool bridge is not implemented for this benchmark.",
        },
    }


def main() -> None:
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run("server.app:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
