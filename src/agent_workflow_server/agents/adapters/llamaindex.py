# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import inspect
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from llama_index.core.workflow import (
    Context,
    Workflow,
)
from llama_index.core.workflow.events import Event
from llama_index.core.workflow.handler import WorkflowHandler
from pydantic import BaseModel

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.generated.manifest.models.agent_deployment import (
    AgentDeployment,
)
from agent_workflow_server.services.message import Message
from agent_workflow_server.services.thread_state import ThreadState
from agent_workflow_server.storage.models import Run
from agent_workflow_server.utils.tools import load_from_module


class LlamaIndexCheckpoint(BaseModel):
    checkpoint_id: UUID
    context: Dict


class LlamaIndexAdapter(BaseAdapter):
    def load_agent(
        self,
        agent: object,
        manifest: AgentDeployment,
        set_thread_persistance_flag: Optional[callable],
    ) -> Optional[BaseAgent]:
        if callable(agent) and len(inspect.signature(agent).parameters) == 0:
            result = agent()
            if isinstance(result, Workflow):
                return LlamaIndexAgent(result, manifest)
        if isinstance(agent, Workflow):
            return LlamaIndexAgent(agent, manifest)
        return None


class InterruptInfo:
    def __init__(self, interrupt_event: Event, resume_event: Event):
        self.interrupt_event = interrupt_event
        self.resume_event = resume_event


class LlamaIndexAgent(BaseAgent):
    def __init__(self, agent: Workflow, manifest: AgentDeployment):
        self.agent = agent
        self.manifest = manifest
        self.interrupts_dict: Dict[str, InterruptInfo] = self._load_interrupts_dict(
            manifest
        )
        self.checkpoints: Dict[str, List[LlamaIndexCheckpoint]] = {}

    def _load_interrupts_dict(
        self, manifest: AgentDeployment
    ) -> Dict[str, InterruptInfo]:
        interrupts_info = manifest.deployment_options[
            0
        ].actual_instance.framework_config.actual_instance.interrupts
        interrupts_dict = {}
        if not interrupts_info:
            return {}
        for interrupt_name, refs in interrupts_info.items():
            interrupt_module_str, interrupt_obj_str = refs.interrupt_ref.split(":", 1)
            resume_module_str, resume_obj_str = refs.resume_ref.split(":", 1)
            interrupt_event = load_from_module(interrupt_module_str, interrupt_obj_str)
            resume_event = load_from_module(resume_module_str, resume_obj_str)
            if not issubclass(interrupt_event, Event):
                raise ValueError(
                    f"Interrupt event {interrupt_event} is not a valid Event class."
                )
            if not issubclass(resume_event, Event):
                raise ValueError(
                    f"Resume event {resume_event} is not a valid Event class."
                )
            interrupts_dict[interrupt_name] = InterruptInfo(
                interrupt_event=interrupt_event, resume_event=resume_event
            )
        return interrupts_dict

    def _is_known_interrupt(self, event: Any):
        for interrupt_info in self.interrupts_dict.values():
            if isinstance(event, interrupt_info.interrupt_event):
                return True
        return False

    async def astream(self, run: Run):
        input = run["input"]
        checkpoints = self.checkpoints.get(run["thread_id"])
        last_checkpoint = checkpoints[-1] if checkpoints else None

        handler: WorkflowHandler = self.agent.run(
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
            interrupt_name = run["interrupt"]["name"]
            event = self.interrupts_dict[interrupt_name].resume_event
            handler.ctx.send_event(event.model_validate(user_data))

        async for event in handler.stream_events():
            if checkpoints is None:
                checkpoints = []

            checkpoints.append(
                LlamaIndexCheckpoint(
                    checkpoint_id=uuid4(),
                    context=handler.ctx.to_dict(),
                )
            )
            self.checkpoints[run["thread_id"]] = checkpoints
            if self._is_known_interrupt(event):
                # Send the interrupt
                await handler.cancel_run()
                yield Message(type="interrupt", data=event.model_dump(mode="json"))
            else:
                yield Message(
                    type="message",
                    data=event.model_dump(mode="json"),
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
