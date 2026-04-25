---
title: Multi-Agent Incident Response OpenEnv
emoji: "🚨"
colorFrom: yellow
colorTo: red
sdk: docker
pinned: false
tags:
  - openenv
  - incident-response
  - fastapi
  - simulation
---

# Multi-Agent Incident Response OpenEnv

This project packages a multi-agent incident-response environment as a real OpenEnv environment backed by the official `openenv-core` runtime.

The environment runs three cooperating roles:
- **Manager Agent**: prioritizes and assigns work.
- **Monitor Agent**: scans logs continuously, detects incidents, and reports findings.
- **Engineer Agent**: inspects code, implements fixes, and validates completion.

The environment introduces schema drift mid-episode and uses strict anti-hallucination penalties.
Rewards are always clamped to `[0.0, 1.0]` and tracked per agent.
 
## OpenEnv Integration

- Runtime package: `openenv-core==0.2.3` (latest PyPI release on March 28, 2026)
- Server base class: `openenv.core.env_server.interfaces.Environment`
- HTTP app wrapper: `openenv.core.env_server.create_app(...)`
- Typed client: [`client.py`](</c:/Users/sharm/Desktop/finale/client.py>)

UI endpoints:
- `/ops-center` -> custom incident command-center landing page.
- `/web/` -> OpenEnv interactive web UI.

## Published links

- GitHub: https://github.com/chirayugk/incident-response-openenv
- Hugging Face Space: https://huggingface.co/spaces/arzunn/incident-response-openenv

## Python Usage

```python
from incident_response_openenv import IncidentAction, IncidentResponseEnv

with IncidentResponseEnv(
    base_url="https://arzunn-incident-response-openenv.hf.space"
).sync() as env:
    reset_result = env.reset()
    obs = reset_result.observation
    role = obs.turn_agent

    # Example role-aware action
    step_result = env.step(
        IncidentAction(
            agent=role,
            action="triage_backlog" if role == "manager" else "scan_logs",
            note="starter move",
        )
    )
    print(step_result.observation.team_rewards)
    print(step_result.observation.metadata["hallucination_count"])
```

## Local run

```bash
pip install -e .
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

In PowerShell, enable the OpenEnv web UI first with `$env:ENABLE_WEB_INTERFACE = "true"`.

Open:
- `http://localhost:7860/ops-center` for the custom dashboard UI.
- `http://localhost:7860/web/` for OpenEnv interaction.
