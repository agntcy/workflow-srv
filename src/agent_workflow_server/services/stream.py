# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import AsyncGenerator

from agent_workflow_server.agents.load import get_agent_info
from agent_workflow_server.storage.models import Run

from .runs import Message


async def stream_run(run: Run) -> AsyncGenerator[Message, None]:
    agent = get_agent_info(run["agent_id"]).agent
    async for event in agent.astream(input=run["input"], config=run["config"]):
        yield Message(
            topic="message",
            data=event,
        )
