# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import inspect
from typing import Optional

from llama_index.core.workflow import Workflow

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.services.message import Message
from agent_workflow_server.storage.models import Run


class LlamaIndexAdapter(BaseAdapter):
    def load_agent(self, agent: object) -> Optional[BaseAgent]:
        if callable(agent) and len(inspect.signature(agent).parameters) == 0:
            result = agent()
            if isinstance(result, Workflow):
                return LlamaIndexAgent(result)
        if isinstance(agent, Workflow):
            return LlamaIndexAgent(agent)
        return None


class LlamaIndexAgent(BaseAgent):
    def __init__(self, agent: Workflow):
        self.agent = agent

    async def astream(self, run: Run):
        input = run["input"]
        handler = self.agent.run(**input)
        async for event in handler.stream_events():
            yield Message(
                type="message",
                data=event,
            )
        final_result = await handler
        yield Message(
            type="message",
            data=final_result,
        )
