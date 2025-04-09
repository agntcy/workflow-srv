# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from agent_workflow_server.agents.agentless import (
    Agentless,
    AgentlessAgentConfig,
    AgentlessRunConfig,
    AgentlessRunInput,
)
from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.services.message import Message
from agent_workflow_server.storage.models import Run


class DummyAgentless: ...


dummyagent = DummyAgentless()


class AgentlessAdapter(BaseAdapter):
    def load_agent(self, agent: object, manifest: dict) -> Optional[BaseAgent]:
        if isinstance(agent, DummyAgentless):
            return AgentlessAgent(manifest)
        return None


class AgentlessAgent(BaseAgent):
    def __init__(self, manifest: dict):
        self.agent = Agentless(config=AgentlessAgentConfig.model_validate(manifest))
        print("Agentless agent loaded with manifest:", manifest)

    async def astream(self, run: Run):
        resp = await self.agent.ainvoke(
            input=AgentlessRunInput(run.input), config=AgentlessRunConfig(run.config)
        )
        yield Message(
            type="message",
            data=resp.messages,
        )
