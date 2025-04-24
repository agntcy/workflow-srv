# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from langchain_core.runnables import RunnableConfig
from langgraph.constants import INTERRUPT
from langgraph.graph.graph import CompiledGraph, Graph
from langgraph.types import Command

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.services.message import Message
from agent_workflow_server.storage.models import Run, ThreadState


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
        configurable = config.get("configurable")
        if configurable is None:
            configurable = {}
        configurable.setdefault("thread_id", run["thread_id"])

        # If there's an interrupt answer, ovverride the input
        if "interrupt" in run and "user_data" in run["interrupt"]:
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

    async def get_state_snapshot(self, thread_id):
        """Returns the thread state snapshot associated with the agent."""
        print(f"Getting state snapshot: {thread_id}")
        config = {}
        configurable = config.get("configurable")
        if configurable is None:
            configurable = {}
        configurable.setdefault("thread_id", thread_id)

        config = RunnableConfig(configurable=configurable, tags=None)

        snapshot = await self.agent.aget_state(config=config)

        return ThreadState(
            checkpoint_id=snapshot.config["configurable"]["checkpoint_id"],
            values=snapshot.values,
            metadata=snapshot.metadata,
        )

    async def get_history(self, thread_id):
        """Returns the history of the thread associated with the agent."""
        print(f"Getting history: {thread_id}")
        config = {}
        configurable = config.get("configurable")
        if configurable is None:
            configurable = {}
        configurable.setdefault("thread_id", thread_id)

        config = RunnableConfig(configurable=configurable, tags=None)

        # Collect history items from the async generator
        history = []
        async for item in self.agent.aget_state_history(config=config):
            history.append(
                ThreadState(
                    checkpoint_id=item.config["configurable"]["checkpoint_id"],
                    values=item.values,
                    metadata=item.metadata,
                )
            )

        return history
