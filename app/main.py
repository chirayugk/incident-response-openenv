from fastapi import FastAPI

from app.env import IncidentEnv
from app.models import Action


app = FastAPI(title="Incident Response API")
env = IncidentEnv()


@app.get("/reset")
def reset():
    return env.reset().model_dump()


@app.post("/step")
def step(action: Action):
    observation, reward, done, info = env.step(action.action)
    return {
        "state": observation.model_dump(),
        "reward": reward,
        "done": done,
        "info": info,
    }
