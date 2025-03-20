import logging
from typing import Any

import jsonschema

from agent_workflow_server.agents.load import AGENTS
from agent_workflow_server.generated.models.run_create import RunCreate

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
            schema=schemas["output"].get("properties", schemas["output"]),
            error_prefix=f"Output validation failed for run {run_id}",
        )


def validate_run_create(run_create: RunCreate) -> RunCreate:
    """Validate RunCreate input against agent's descriptor schema"""
    schemas = get_agent_schemas(run_create.agent_id)
    if run_create.input:
        validate_against_schema(run_create.input, schemas["input"])

    if run_create.config:
        validate_against_schema(run_create.config, schemas["config"])

    return run_create
