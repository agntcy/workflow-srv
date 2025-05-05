# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import inspect
from typing import Dict, Optional

from llama_index.core.workflow import (
    Context,
    HumanResponseEvent,
    InputRequiredEvent,
    Workflow,
)

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.services.message import Message
from agent_workflow_server.storage.models import Run


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
        self.contexts: Dict[str, Dict] = {}

    async def astream(self, run: Run):
        input = run["input"]
        ctx_data = self.contexts.get(run["thread_id"])

        handler = self.agent.run(
            ctx=Context.from_dict(self.agent, ctx_data) if ctx_data else None,
            input={**input},
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
            self.contexts[run["thread_id"]] = handler.ctx.to_dict()
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
