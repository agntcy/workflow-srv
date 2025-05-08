# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import inspect
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from llama_index.core.workflow import (
    Context,
    HumanResponseEvent,
    InputRequiredEvent,
    Workflow,
)
from pydantic import BaseModel

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.services.message import Message
from agent_workflow_server.services.thread_state import ThreadState
from agent_workflow_server.storage.models import Run


class LlamaIndexCheckpoint(BaseModel):
    checkpoint_id: UUID
    context: Dict


class LlamaIndexAdapter(BaseAdapter):
    def load_agent(
        self, agent: object, set_thread_persistance_flag: Optional[callable]
    ) -> Optional[BaseAgent]:
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
        self.checkpoints: Dict[str, List[LlamaIndexCheckpoint]] = {}

    async def astream(self, run: Run):
        input = run["input"]
        checkpoints = self.checkpoints.get(run["thread_id"])
        last_checkpoint = checkpoints[-1] if checkpoints else None

        handler = self.agent.run(
            ctx=Context.from_dict(self.agent, last_checkpoint.context)
            if last_checkpoint and last_checkpoint.context
            else None,
            **input,
        )
        if handler.ctx is None:
            # This should never happen, workflow.run actually sets the Context
            raise ValueError("Context cannot be None.")

        if "interrupt" in run and "user_data" in run["interrupt"]:
            user_data = run["interrupt"]["user_data"]

            # FIXME: workaround to extract the user response from a dict/obj. Needed for input validation, remove once not needed anymore.
            if isinstance(user_data, dict) and len(user_data) == 1:
                user_data = list(user_data.values())[0]
            else:
                raise ValueError(
                    f"Invalid interrupt response: {user_data}. Expected a dictionary with a single key."
                )
            handler.ctx.send_event(HumanResponseEvent(response=user_data))

        async for event in handler.stream_events():
            if checkpoints is None:
                checkpoints = []

            checkpoints.append(
                LlamaIndexCheckpoint(
                    checkpoint_id=uuid4(),
                    context=handler.ctx.to_dict(),
                )
            )
            if isinstance(event, InputRequiredEvent):
                # Send the interrupt
                await handler.cancel_run()
                # FIXME: workaround to wrap the prefix (str) in a dict/obj. Needed for output validation, remove once not needed anymore.
                yield Message(type="interrupt", data={"interrupt": event.prefix})
            else:
                yield Message(
                    type="message",
                    data=event,
                )
        final_result = await handler
        checkpoints.append(
            LlamaIndexCheckpoint(
                checkpoint_id=uuid4(),
                context=handler.ctx.to_dict(),
            )
        )
        self.checkpoints[run["thread_id"]] = checkpoints
        yield Message(
            type="message",
            data=final_result,
        )

    async def get_agent_state(self, thread_id):
        checkpoints = self.checkpoints.get(thread_id)
        # If there are no checkpoints, return None
        if not checkpoints:
            return None

        # Get the last checkpoint
        last_checkpoint = checkpoints[-1]
        # If the last checkpoint has a context, return its values
        return ThreadState(
            values=last_checkpoint.context,
            checkpoint_id=last_checkpoint.checkpoint_id,
        )

    async def get_history(self, thread_id, limit, before):
        checkpoints = self.checkpoints.get(thread_id)
        # If there are no checkpoints, return empty list
        if not checkpoints:
            return []

        # If before is not None, filter the checkpoints
        if before:
            checkpoints = [
                checkpoint
                for checkpoint in checkpoints
                if checkpoint.checkpoint_id < before
            ]
        # If limit is not None, limit the number of checkpoints
        if limit:
            checkpoints = checkpoints[:limit]

        # Convert the checkpoints to a list of ThreadState objects
        history = [
            ThreadState(
                values=checkpoint.context, checkpoint_id=str(checkpoint.checkpoint_id)
            )
            for checkpoint in checkpoints
        ]

        return history

    async def update_agent_state(self, thread_id, state):
        # Check is state value can be converted to a Context
        try:
            ctx = Context.from_dict(self.agent, state["values"])
        except Exception as e:
            raise ValueError(
                f"Failed to update agent state for thread {thread_id}: {e}"
            )

        # Get the checkpoints for the thread
        checkpoints = self.checkpoints.get(thread_id)
        # If there are no checkpoints, create a new list
        if checkpoints is None:
            checkpoints = []

        # Append the new checkpoint to the list of checkpoints
        checkpoints.append(
            LlamaIndexCheckpoint(
                checkpoint_id=uuid4(),
                context=ctx.to_dict(),
            )
        )
        self.checkpoints[thread_id] = checkpoints

        return await self.get_agent_state(thread_id)
