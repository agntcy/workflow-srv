# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import inspect
import json
from typing import Dict, List, Optional

from llama_index.core.workflow import (
    Context,
    HumanResponseEvent,
    InputRequiredEvent,
    Workflow,
)

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.services.message import Message
from agent_workflow_server.services.thread_state import ThreadState
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
        """
        Note: The broker_log is a List[Event] in the Context class.
        It contais a list of events that are generated during the workflow execution.
        If these are pydantic models, they will be serialized to JSON strings.
        The last item in the broker_log is the most recent event.
        """
        ctx_data = self.contexts.get(thread_id)
        ## Get the broker_log vale of the context if it exists
        if ctx_data and "broker_log" in ctx_data:
            broker_log = ctx_data["broker_log"]
            # if broker_log exists and is a list, get the last item
            if broker_log and isinstance(broker_log, List):
                last_broker_log = broker_log[-1]

                ## Check if the last_broker_log exists and is a string
                if last_broker_log and isinstance(last_broker_log, str):
                    try:
                        # Parse the JSON string
                        parsed_data = json.loads(last_broker_log)
                        # Check if it's a Pydantic model serialization
                        if isinstance(parsed_data, dict) and parsed_data.get(
                            "__is_pydantic"
                        ):
                            # Return the "value" field of the Pydantic model
                            # The content of this is defined by the Agent
                            threadStateValue = parsed_data.get("value")

                            if threadStateValue:
                                return ThreadState(
                                    values=threadStateValue,
                                )
                        else:
                            # If its not a pydantic return None
                            return None
                    except json.JSONDecodeError:
                        # If it's not valid JSON, return None
                        return None

        return None

    async def get_history(self, thread_id, limit, before):
        '''
        Note: See note in get_agent_state
        '''
        # Get context data for the given thread_id
        ctx_data = self.contexts.get(thread_id)
        # If context data exists, check for broker_log
        if ctx_data and "broker_log" in ctx_data:
            broker_log = ctx_data["broker_log"]
            # If broker_log exists and is a list, return the last 'limit' items
            if broker_log and isinstance(broker_log, List):
                # Return the last 'limit' items from the broker_log
                log_items = broker_log[-limit:]
                # If 'before' is provided, filter the log items
                if before:
                    log_items = [item for item in log_items if item < before]

                # Parse each log item as JSON to ThreadState
                parsed_log_items = []
                for item in log_items:
                    # Check if the item is a string
                    if isinstance(item, str):
                        # Parse the JSON string
                        # Check if the item is a Pydantic model serialization
                        try:
                            parsed_data = json.loads(item)
                            if isinstance(parsed_data, dict) and parsed_data.get(
                                "__is_pydantic"
                            ):
                                threadStateValue = parsed_data.get("value")
                                if threadStateValue:
                                    parsed_log_items.append(
                                        ThreadState(
                                            values=threadStateValue,
                                            checkpoint_id="",
                                        )
                                    )
                        except json.JSONDecodeError:
                            # If it's not valid JSON, skip this item
                            continue

                return parsed_log_items

        # If no context data or broker_log exists, return an empty list
        return []

    async def update_agent_state(self, thread_id, state):
        pass
