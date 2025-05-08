# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import inspect
from typing import Any, Dict, Optional

from llama_index.core.workflow import (
    Context,
    Workflow,
)
from llama_index.core.workflow.events import Event
from llama_index.core.workflow.handler import WorkflowHandler

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.generated.manifest.models.agent_manifest import AgentManifest
from agent_workflow_server.services.message import Message
from agent_workflow_server.storage.models import Run
from agent_workflow_server.utils.tools import load_from_module


class LlamaIndexAdapter(BaseAdapter):
    def load_agent(
        self,
        agent: object,
        manifest: AgentManifest,
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
    def __init__(self, agent: Workflow, manifest: AgentManifest):
        self.agent = agent
        self.manifest = manifest
        self.contexts: Dict[str, Dict] = {}
        self.interrupts_dict: Dict[str, InterruptInfo] = self._load_interrupts_dict(
            manifest
        )

    def _load_interrupts_dict(
        self, manifest: AgentManifest
    ) -> Dict[str, InterruptInfo]:
        interrupts_info = manifest.deployment.deployment_options[
            0
        ].actual_instance.framework_config.actual_instance.interrupts
        interrupts_dict = {}
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
        ctx_data = self.contexts.get(run["thread_id"])

        handler: WorkflowHandler = self.agent.run(
            ctx=Context.from_dict(self.agent, ctx_data) if ctx_data else None,
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
            self.contexts[run["thread_id"]] = handler.ctx.to_dict()
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
        self.contexts[run["thread_id"]] = handler.ctx.to_dict()
        yield Message(
            type="message",
            data=final_result,
        )

    async def get_agent_state(self, thread_id):
        pass

    async def get_history(self, thread_id, limit, before):
        pass

    async def update_agent_state(self, thread_id, state):
        pass
