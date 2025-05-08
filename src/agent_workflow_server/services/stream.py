# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import AsyncGenerator, List

import jsonschema

from agent_workflow_server.agents.load import get_agent_info
from agent_workflow_server.generated.models.agent_acp_spec_interrupts_inner import (
    AgentACPSpecInterruptsInner,
)
from agent_workflow_server.storage.models import Run

from .runs import Message


def _insert_interrupt_name(
    interrupts: List[AgentACPSpecInterruptsInner], interrupt_message: Message
):
    """
    Iterates over the 'interrupt' schema in the ACP Descriptor to find the interrupt name, and inserts it into the Message.
    """
    for interrupt in interrupts:
        # Return the first interrupt_type that validates the json schema
        try:
            jsonschema.validate(
                instance=interrupt_message.data, schema=interrupt.interrupt_payload
            )
            interrupt_message.interrupt_name = interrupt.interrupt_type
            break
        except jsonschema.ValidationError:
            # If the validation fails, continue and try the next one
            continue
    else:
        raise ValueError(
            f"Interrupt schemas mismatch: could not find matching interrupt type for the received interrupt payload: {interrupt_message.data}. Check the interrupts schemas in the ACP Descriptor."
        )

    return interrupt_message


async def stream_run(run: Run) -> AsyncGenerator[Message, None]:
    agent_info = get_agent_info(run["agent_id"])
    agent = agent_info.agent
    async for message in agent.astream(run=run):
        if message.type == "interrupt":
            message = _insert_interrupt_name(
                agent_info.acp_descriptor.specs.interrupts, message
            )
        yield message
