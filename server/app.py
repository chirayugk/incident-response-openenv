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
      body {
        margin: 0;
        font-family: Inter, Segoe UI, sans-serif;
        background: radial-gradient(circle at top, #17162e, #07080f 55%);
        color: #ecf0ff;
      }
      .wrap { max-width: 1040px; margin: 36px auto; padding: 0 18px; }
      .hero { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 18px; padding: 22px; }
      .title { font-size: 30px; font-weight: 700; margin: 0 0 8px; }
      .subtitle { color: #b7c1ff; margin: 0; }
      .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 18px; }
      .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; padding: 14px; }
      .role { font-size: 12px; letter-spacing: 0.08em; color: #8fd4ff; text-transform: uppercase; margin-bottom: 8px; }
      .actions { font-size: 14px; color: #d6dcff; line-height: 1.45; }
      .pill { display:inline-block; padding: 4px 9px; border-radius: 999px; font-size: 12px; margin-right: 6px; margin-top: 6px; }
      .ok { background: #234f31; color: #b8ffd3; }
      .warn { background: #5b3e1e; color: #ffd6a6; }
      a { color: #8fd4ff; }
    </style>
  </head>
  <body>
    <div class="wrap">
      <section class="hero">
        <h1 class="title">Multi-Agent Incident Ops Center</h1>
        <p class="subtitle">
          Manager AI prioritizes work, Monitor AI scans logs and reports incidents, Engineer AI executes fixes and tests.
        </p>
        <div style="margin-top: 12px;">
          <span class="pill ok">Rewards in [0,1] per agent</span>
          <span class="pill warn">Hallucination/Cheating penalties enabled</span>
        </div>
        <p style="margin-top: 12px;">
          Use the OpenEnv interface at <a href="/web/">/web/</a> for interactive episodes.
        </p>
      </section>
      <section class="grid">
        <article class="card">
          <div class="role">Manager Agent</div>
          <div class="actions">triage_backlog, assign_bugfix, assign_investigation, reprioritize</div>
        </article>
        <article class="card">
          <div class="role">Monitor Agent</div>
          <div class="actions">scan_logs, alert_incident, verify_fix</div>
        </article>
        <article class="card">
          <div class="role">Engineer Agent</div>
          <div class="actions">inspect_code, implement_fix, write_test, claim_done</div>
        </article>
      </section>
    </div>
  </body>
</html>
"""
    )


def main(host: str = "0.0.0.0", port: int | None = None) -> None:
    uvicorn.run(app, host=host, port=port or int(os.getenv("PORT", "7860")))


if __name__ == "__main__":
    main()
