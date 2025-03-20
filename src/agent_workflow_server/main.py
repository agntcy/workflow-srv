import asyncio
import logging
import os
import signal
import sys

import uvicorn
import uvicorn.logging
from dotenv import load_dotenv
from fastapi import Depends, FastAPI

from agent_workflow_server.agents.load import load_agents
from agent_workflow_server.apis.agents import router as AgentsApiRouter
from agent_workflow_server.apis.runs import router as RunsApiRouter

from agent_workflow_server.agents.load import register_from_env
from agent_workflow_server.depends.authentication import (
    authentication_with_api_key,
    setup_api_key_auth,
)

from agent_workflow_server.logger.custom_logger import CustomLoggerHandler
from agent_workflow_server.services.queue import start_workers

load_dotenv()

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000

logging.basicConfig(level=logging.INFO, handlers=[CustomLoggerHandler], force=True)

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
    router=RunsApiRouter,
    dependencies=[Depends(authentication_with_api_key)],
)


def signal_handler(sig, frame):
    logger.warning(f"Received {signal.Signals(sig).name}. Exiting...")
    sys.exit(0)


def start():
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        load_agents()
        n_workers = int(os.environ.get("NUM_WORKERS", 5))

        loop = asyncio.get_event_loop()
        loop.create_task(start_workers(n_workers))

        config = uvicorn.Config(
            app,
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
