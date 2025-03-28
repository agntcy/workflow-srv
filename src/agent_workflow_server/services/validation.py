# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any

import jsonschema

from agent_workflow_server.agents.load import AGENTS
from agent_workflow_server.generated.models.run_create_stateless import (
    RunCreateStateless,
)

logger = logging.getLogger(__name__)


class InvalidFormatException(Exception):
    """Raised when schema validation fails"""

    pass


def validate_against_schema(
    instance: Any, schema: dict, error_prefix: str = ""
) -> None:
    """Validate an instance against a JSON schema"""
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"{error_prefix}: {str(e)}")
        raise InvalidFormatException(f"{error_prefix}: {str(e)}")


def get_agent_schemas(agent_id: str):
    """Get input, output and config schemas for an agent"""
    agent_info = AGENTS.get(agent_id)

    specs = agent_info.manifest.specs
    return {"input": specs.input, "output": specs.output, "config": specs.config}


def validate_output(run_id, agent_id: str, output: Any) -> None:
    if output:
        schemas = get_agent_schemas(agent_id)

        validate_against_schema(
            instance=output,
            schema=schemas["output"],
            error_prefix=f"Output validation failed for run {run_id}",
        )


def validate_run_create(run_create: RunCreateStateless) -> RunCreateStateless:
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
