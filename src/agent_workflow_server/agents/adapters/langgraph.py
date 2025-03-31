# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from langchain_core.runnables import RunnableConfig
from langgraph.constants import INTERRUPT
from langgraph.graph.graph import CompiledGraph, Graph
from langgraph.types import Command

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.services.message import Message
from agent_workflow_server.storage.models import Run


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

    async def astream(self, run: Run):
        input = run["input"]
        config = run["config"]
        if config is None:
            config = {}
        configurable = config["configurable"]
        if configurable is None:
            configurable = {}
        configurable.setdefault("thread_id", run["thread_id"])

        # If there's an interrupt answer, ovverride the input
        if run.get("interrupt") is not None and run["interrupt"].get("user_data"):
            input = Command(resume=run["interrupt"]["user_data"])

        async for event in self.agent.astream(
            input=input,
            config=RunnableConfig(
                configurable=configurable,
                tags=config["tags"],
                recursion_limit=config["recursion_limit"],
            ),
        ):
            for k, v in event.items():
                if k == INTERRUPT:
                    yield Message(
                        type="interrupt",
                        event=k,
                        data=v[0].value,
                    )
                else:
                    yield Message(
                        type="message",
                        event=k,
                        data=v,
                    )
