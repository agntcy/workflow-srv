# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent

# Make sure that this and the one in the .env.test file are the same
MOCK_AGENT_ID = "3f1e2549-5799-4321-91ae-2a4881d55526"

MOCK_RUN_INPUT = {"message": "What's the color of the sky?"}
MOCK_RUN_OUTPUT = {"message": "The color of the sky is blue"}


class MockAgentImpl: ...


class MockAgent(BaseAgent):
    def __init__(self, agent: MockAgentImpl):
        self.agent = agent

    async def astream(self, input: dict, config: dict):
        await asyncio.sleep(3)
        yield MOCK_RUN_OUTPUT


class MockAdapter(BaseAdapter):
    def load_agent(self, agent: object):
        if isinstance(agent, MockAgentImpl):
            return MockAgent(agent)


mock_agent = MockAgentImpl()
