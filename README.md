---
title: Incident Response OpenEnv
emoji: "🚨"
colorFrom: orange
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

This project packages a small incident-response environment as a Docker-ready FastAPI app with a built-in frontend for Hugging Face Spaces.

The environment starts with timeout logs, introduces a schema drift on step three, and rewards agents that inspect the logs before resolving the issue efficiently.

## Published links

- GitHub: https://github.com/chirayugk/incident-response-openenv
- Hugging Face Space: https://huggingface.co/spaces/arzunn/incident-response-openenv

## Local run

```bash
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload
```

Open `http://localhost:7860` to use the frontend.
