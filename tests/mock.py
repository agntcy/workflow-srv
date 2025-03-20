import asyncio

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent

MOCK_AGENT_ID = "3f1e2549-5799-4321-91ae-2a4881d55526"

MOCK_AGENTS_REF_ENV = {
    "AGENTS_REF": '{{"{0}": "tests.mock:mock_agent"}}'.format(MOCK_AGENT_ID)
}

MOCK_MANIFEST_ENV = {"AGENT_MANIFEST_PATH": "tests/mock_manifest.json"}
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
