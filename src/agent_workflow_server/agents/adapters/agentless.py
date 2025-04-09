# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
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

logger = logging.getLogger(__name__)


class AgentlessAdapter(BaseAdapter):
    def load_agent(self, agent: object, manifest: dict) -> Optional[BaseAgent]:
        if isinstance(agent, DummyAgentless):
            return AgentlessAgent(manifest)
        return None


class AgentlessAgent(BaseAgent):
    def __init__(self, manifest: dict):
        config = manifest["deployment"]["deployment_options"][0]["framework_config"][
            "config"
        ]
        self.agent = Agentless(config=AgentlessAgentConfig.model_validate(config))
        logger.debug("Agentless agent loaded with manifest %s", manifest)

    async def astream(self, run: Run):
        resp = await self.agent.ainvoke(
            input=AgentlessRunInput.model_validate(run["input"]),
            config=AgentlessRunConfig.model_validate(run["config"]),
        )
        yield Message(
            type="message",
            data=resp.messages,
        )
