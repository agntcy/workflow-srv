# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from typing import AsyncGenerator

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.services.message import Message
from agent_workflow_server.storage.models import Run

# Make sure that this and the one in the .env.test file are the same
MOCK_AGENT_ID = "3f1e2549-5799-4321-91ae-2a4881d55526"

MOCK_RUN_INPUT = {"message": "What's the color of the sky?"}
MOCK_RUN_OUTPUT = {"message": "The color of the sky is blue"}

MOCK_RUN_INPUT_INTERRUPT = {"message": "Please interrupt"}
MOCK_RUN_EVENT_INTERRUPT = "__mock_interrupt__"
MOCK_RUN_OUTPUT_INTERRUPT = {"message": "How can I help you?"}


class MockAgentImpl: ...


class MockAgent(BaseAgent):
    def __init__(self, agent: MockAgentImpl):
        self.agent = agent

    async def astream(self, run: Run) -> AsyncGenerator[Message, None]:
        if run["input"] == MOCK_RUN_INPUT or (
            run.get("interrupt") is not None
            and run["interrupt"].get("user_data") == MOCK_RUN_INPUT
        ):
            await asyncio.sleep(3)
            yield Message(type="message", data=MOCK_RUN_OUTPUT)
            return
        if run["input"] == MOCK_RUN_INPUT_INTERRUPT:
            yield Message(
                type="interrupt",
                event=MOCK_RUN_EVENT_INTERRUPT,
                data=MOCK_RUN_OUTPUT_INTERRUPT,
            )


class MockAdapter(BaseAdapter):
    def load_agent(self, agent: object, manifest: dict):
        if isinstance(agent, MockAgentImpl):
            return MockAgent(agent)


mock_agent = MockAgentImpl()
