---
title: Incident Response OpenEnv
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

# Incident Response OpenEnv

This project packages a small incident-response environment as a real OpenEnv environment backed by the official `openenv-core` runtime.

The environment starts with timeout logs, introduces a schema drift on step three, and rewards agents that inspect the logs before resolving the issue efficiently.

## OpenEnv Integration

- Runtime package: `openenv-core==0.2.3` (latest PyPI release on March 28, 2026)
- Server base class: `openenv.core.env_server.interfaces.Environment`
- HTTP app wrapper: `openenv.core.env_server.create_app(...)`
- Typed client: [`client.py`](</c:/Users/sharm/Desktop/finale/client.py>)

The Docker image enables `ENABLE_WEB_INTERFACE=true`, so the Space root redirects to OpenEnv's built-in `/web/` interface.

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
    step_result = env.step(IncidentAction(action="check_logs"))
    print(reset_result.observation.logs)
    print(step_result.reward, step_result.observation.done)
```

## Local run

```bash
pip install -e .
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

In PowerShell, enable the OpenEnv web UI first with `$env:ENABLE_WEB_INTERFACE = "true"`.

Open `http://localhost:7860` and it will redirect to the OpenEnv web UI.
