from __future__ import annotations

import os

import uvicorn
from openenv.core.env_server import create_app

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
    env_name="incident_response_openenv",
    max_concurrent_envs=4,
)


def main(host: str = "0.0.0.0", port: int | None = None) -> None:
    uvicorn.run(app, host=host, port=port or int(os.getenv("PORT", "7860")))


if __name__ == "__main__":
    main()
