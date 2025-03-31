# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import AsyncGenerator

from agent_workflow_server.agents.load import get_agent_info
from agent_workflow_server.storage.models import Run

from .runs import Message


async def stream_run(run: Run) -> AsyncGenerator[Message, None]:
    agent_info = get_agent_info(run["agent_id"])
    agent = agent_info.agent
    if agent_info.manifest.specs.capabilities.interrupts:
        # TODO: This will only work for langgraph
        if run.get("config") is None:
            run["config"] = {}
        if run["config"].get("configurable") is None:
            run["config"]["configurable"] = {}
        run["config"]["configurable"].setdefault("thread_id", run["thread_id"])

    async for message in agent.astream(input=run["input"], config=run["config"]):
        yield message
