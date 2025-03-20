import logging
import jsonschema
from typing import Any

from agent_workflow_server.agents.load import AGENTS

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
