from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal

import environment as env

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Incident Response Multi-Agent System",
    description="A multi-agent incident response simulation backend.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class StepRequest(BaseModel):
    agent: Literal["manager", "monitor", "engineer"]
    action: str
    message: str


class RunRequest(BaseModel):
    steps: int = 10

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/state", summary="Get full environment state")
def get_state():
    return env.get_state()


@app.post("/step", summary="Manual agent step")
def step(req: StepRequest):
    try:
        result = env.manual_step(req.agent, req.action, req.message)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/run_agents", summary="Start autonomous agent loop")
async def run_agents(req: RunRequest, background_tasks: BackgroundTasks):
    if env.is_running():
        raise HTTPException(status_code=409, detail="Autonomous loop is already running.")
    background_tasks.add_task(env.run_autonomous, req.steps)
    return {"detail": f"Autonomous loop started for {req.steps} steps."}


@app.post("/stop_agents", summary="Stop autonomous agent loop")
def stop_agents():
    env.stop_autonomous()
    return {"detail": "Stop signal sent. Loop will halt at next check."}


@app.post("/reset", summary="Reset environment to initial state")
def reset():
    env.reset_state()
    return {"detail": "Environment reset successfully.", "state": env.get_state()}
