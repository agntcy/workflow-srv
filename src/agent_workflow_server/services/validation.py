# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, List

import jsonschema

from agent_workflow_server.agents.load import AGENTS
from agent_workflow_server.generated.models.agent_acp_spec_interrupts_inner import (
    AgentACPSpecInterruptsInner,
)
from agent_workflow_server.generated.models.run_create_stateful import (
    RunCreateStateful,
)
from agent_workflow_server.generated.models.run_create_stateless import (
    RunCreateStateless,
)
from agent_workflow_server.services.utils import check_run_is_interrupted
from agent_workflow_server.storage.storage import DB

logger = logging.getLogger(__name__)


class InvalidFormatException(Exception):
    """Raised when schema validation fails"""

    pass


def validate_against_schema(
    instance: Any, schema: dict, error_prefix: str = ""
) -> None:
    """Validate an instance against a JSON schema"""
    # Convert Pydantic models to dict if needed
    if hasattr(instance, "model_dump"):
        # For Pydantic v2
        instance = instance.model_dump()
    elif hasattr(instance, "dict"):
        # For Pydantic v1
        instance = instance.dict()
    elif hasattr(instance, "actual_instance") and isinstance(
        instance.actual_instance, dict
    ):
        # This is a workaround for the Pydantic v1 issue where the instance is wrapped
        instance = instance.actual_instance

    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"{error_prefix}: {str(e)}")
        raise InvalidFormatException(f"{error_prefix}: {str(e)}")


def get_agent_schemas(agent_id: str):
    """Get input, output and config schemas for an agent"""
    agent_info = AGENTS.get(agent_id)
    if not agent_info:
        raise ValueError(f"Agent {agent_id} not found")

    specs = agent_info.acp_descriptor.specs
    return {
        "input": specs.input,
        "output": specs.output,
        "config": specs.config,
        "interrupts": specs.interrupts,
    }


def validate_output(run_id, agent_id: str, output: Any) -> None:
    if output:
        schemas = get_agent_schemas(agent_id)

        validate_against_schema(
            instance=output,
            schema=schemas["output"],
            error_prefix=f"Output validation failed for run {run_id}",
        )


def validate_run_create(
    run_create: RunCreateStateless | RunCreateStateful,
) -> RunCreateStateless | RunCreateStateful:
    """Validate RunCreate input against agent's descriptor schema"""
    schemas = get_agent_schemas(run_create.agent_id)
    if schemas["input"] and not run_create.input:
        raise InvalidFormatException('"input" is required for this agent')
    if schemas["config"] and not run_create.config:
        raise InvalidFormatException('"config" is required for this agent')

    if run_create.input:
        validate_against_schema(run_create.input, schemas["input"])

    if run_create.config and run_create.config.configurable:
        validate_against_schema(run_create.config.configurable, schemas["config"])

    return run_create


def validate_resume_run(run_id: str, body: Any):
    run = DB.get_run(run_id)
    check_run_is_interrupted(run)

    interrupt_name = run["interrupt"]["name"]
    interrupts_schemas: List[AgentACPSpecInterruptsInner] = get_agent_schemas(
        run["agent_id"]
    )["interrupts"]

    # Get interrupt_schema given the interrupt_name
    for interrupt_schema in interrupts_schemas:
        if interrupt_schema.interrupt_type == interrupt_name:
            break
    else:
        raise ValueError(f"Interrupt {interrupt_name} not found")

    validate_against_schema(
        body, interrupt_schema.resume_payload, "Resume payload not valid"
    )
