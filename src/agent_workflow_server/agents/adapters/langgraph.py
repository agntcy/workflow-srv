# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph.graph import CompiledGraph, Graph

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.storage.models import Config


class LangGraphAdapter(BaseAdapter):
    def load_agent(self, agent: object) -> Optional[BaseAgent]:
        if isinstance(agent, Graph):
            return LangGraphAgent(agent.compile())
        elif isinstance(agent, CompiledGraph):
            return LangGraphAgent(agent)
        return None


class LangGraphAgent(BaseAgent):
    def __init__(self, agent: CompiledGraph):
        self.agent = agent

    async def astream(self, input: dict, config: Optional[Config]):
        async for event in self.agent.astream(
            input=input,
            config=RunnableConfig(
                configurable=config["configurable"],
                tags=config["tags"],
                recursion_limit=config["recursion_limit"],
            )
            if config
            else None,
            stream_mode="values",
        ):
            yield event
