# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.constants import INTERRUPT
from langgraph.graph.graph import CompiledGraph, Graph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from agent_workflow_server.agents.base import (
    BaseAdapter,
    BaseAgent,
    ThreadsNotSupportedError,
)
from agent_workflow_server.generated.manifest.models.agent_deployment import (
    AgentDeployment,
)
from agent_workflow_server.services.message import Message
from agent_workflow_server.services.thread_state import ThreadState
from agent_workflow_server.storage.models import Run


class LangGraphAdapter(BaseAdapter):
    def load_agent(
        self,
        agent: object,
        manifest: AgentDeployment,
        set_thread_persistance_flag: Optional[callable],
    ) -> Optional[BaseAgent]:
        if isinstance(agent, Graph):
            return LangGraphAgent(agent.compile())
        elif isinstance(agent, CompiledGraph):
            if set_thread_persistance_flag is not None:
                set_thread_persistance_flag(
                    isinstance(agent.checkpointer, PostgresSaver)
                )

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

        # If it's a CompiledStateGraph, validate (and deserialize) input
        if isinstance(self.agent, CompiledStateGraph) and hasattr(
            self.agent.builder.schema, "model_validate"
        ):
            input = self.agent.builder.schema.model_validate(input)

        # If there's an interrupt answer, ovverride the input
        if "interrupt" in run and "user_data" in run["interrupt"]:
            input = Command(resume=run["interrupt"]["user_data"])

        runconfig = RunnableConfig(configurable=configurable)
        if "tags" in config:
            runconfig["tags"] = config["tags"]
        if "recursion_limit" in config:
            runconfig["recursion_limit"] = config["recursion_limit"]

        async for event in self.agent.astream(
            input=input,
            config=runconfig,
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

    async def get_agent_state(self, thread_id):
        """Returns the thread state snapshot associated with the agent."""
        config = RunnableConfig(configurable={"thread_id": thread_id}, tags=None)

        try:
            snapshot = await self.agent.aget_state(config=config)
        except ValueError as e:
            if str(e) == "No checkpointer set":
                raise ThreadsNotSupportedError(
                    "This agent does not support threads."
                ) from e
            else:
                raise e
        ## if snapshot values is empty return None
        if snapshot.values is None or len(snapshot.values) == 0:
            return None
        return ThreadState(
            checkpoint_id=snapshot.config["configurable"]["checkpoint_id"],
            values=snapshot.values,
            metadata=snapshot.metadata,
        )

    async def get_history(self, thread_id, limit, before):
        """Returns the history of the thread associated with the agent."""
        config = RunnableConfig(configurable={"thread_id": thread_id}, tags=None)

        # Collect history items from the async generator
        history = []
        try:
            async for item in self.agent.aget_state_history(
                config=config, limit=limit, before=before
            ):
                history.append(
                    ThreadState(
                        checkpoint_id=item.config["configurable"]["checkpoint_id"],
                        values=item.values,
                        metadata=item.metadata,
                    )
                )
        except ValueError as e:
            if str(e) == "No checkpointer set":
                raise ThreadsNotSupportedError(
                    "This agent does not support threads."
                ) from e
            else:
                raise e

        return history

    async def update_agent_state(self, thread_id, state):
        """Updates the thread state associated with the agent."""
        config = RunnableConfig(configurable={"thread_id": thread_id}, tags=None)

        try:
            await self.agent.aupdate_state(
                config=config,
                values=state["values"],
            )
        except ValueError as e:
            if str(e) == "No checkpointer set":
                raise ThreadsNotSupportedError(
                    "This agent does not support threads."
                ) from e
            else:
                raise e
