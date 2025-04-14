# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import AsyncGenerator

from agent_workflow_server.agents.load import get_agent_info
from agent_workflow_server.storage.models import Run

from .runs import Message


async def stream_run(run: Run) -> AsyncGenerator[Message, None]:
    agent_info = get_agent_info(run["agent_id"])
    agent = agent_info.agent
    async for message in agent.astream(run=run):
        yield message
