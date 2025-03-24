from typing import Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph.graph import CompiledGraph, Graph

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent


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

    async def astream(self, input: dict, config: dict):
        async for event in self.agent.astream(
            input=input,
            config=RunnableConfig(configurable=config),
            stream_mode="values",
        ):
            yield event
