# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import asyncio
import logging
import os
import signal
import sys

import uvicorn
from dotenv import find_dotenv, load_dotenv
from fastapi import Depends, FastAPI

from agent_workflow_server.agents.load import load_agents
from agent_workflow_server.apis.agents import public_router as PublicAgentsApiRouter
from agent_workflow_server.apis.agents import router as AgentsApiRouter
from agent_workflow_server.apis.authentication import (
    authentication_with_api_key,
    setup_api_key_auth,
)
from agent_workflow_server.apis.stateless_runs import router as StatelessRunsApiRouter
from agent_workflow_server.apis.threads import router as ThreadsApiRouter
from agent_workflow_server.apis.threads_runs import router as ThreadRunsApiRouter
from agent_workflow_server.services.queue import start_workers

load_dotenv(dotenv_path=find_dotenv(usecwd=True))

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_NUM_WORKERS = 5
DEFAULT_AGENT_MANIFEST_PATH = "manifest.json"

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agent Workflow Server",
    version="0.1",
)

setup_api_key_auth(app)

app.include_router(
    router=AgentsApiRouter,
    dependencies=[Depends(authentication_with_api_key)],
)
app.include_router(
    router=PublicAgentsApiRouter,
)
app.include_router(
    router=StatelessRunsApiRouter,
    dependencies=[Depends(authentication_with_api_key)],
)

app.include_router(
    router=ThreadsApiRouter,
    dependencies=[Depends(authentication_with_api_key)],
)

app.include_router(
    router=ThreadRunsApiRouter,
    dependencies=[Depends(authentication_with_api_key)],
)


def signal_handler(sig, frame):
    logger.warning(f"Received {signal.Signals(sig).name}. Exiting...")
    sys.exit(0)


def start():
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        agents_ref = os.getenv("AGENTS_REF", None)
        agent_manifest_path = os.getenv(
            "AGENT_MANIFEST_PATH", DEFAULT_AGENT_MANIFEST_PATH
        )
        load_agents(agents_ref, agent_manifest_path)
        n_workers = int(os.environ.get("NUM_WORKERS", DEFAULT_NUM_WORKERS))

        loop = asyncio.get_event_loop()
        loop.create_task(start_workers(n_workers))

        # use module import method to support reload argument
        config = uvicorn.Config(
            "agent_workflow_server.main:app",
            host=os.getenv("API_HOST", DEFAULT_HOST) or DEFAULT_HOST,
            port=int(os.getenv("API_PORT", DEFAULT_PORT)) or DEFAULT_PORT,
            loop="asyncio",
        )
        server = uvicorn.Server(config)
        loop.run_until_complete(server.serve())
    except SystemExit as e:
        logger.warning(f"Agent Workflow Server exited with code: {e}")
    except Exception as e:
        logger.error(f"Exiting due to an unexpected error: {e}")


if __name__ == "__main__":
    start()
