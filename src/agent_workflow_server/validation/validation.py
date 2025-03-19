import logging
import jsonschema
from typing import Any

from agent_workflow_server.agents.load import AGENTS

logger = logging.getLogger(__name__)

class AgentNotFoundException(Exception):
    """Raised when an agent is not found"""
    pass

class InvalidFormatException(Exception):
    """Raised when schema validation fails"""
    pass

class UnprocessableContentException(Exception):
    """Raised when the content is not processable"""
    pass

def validate_against_schema(instance: Any, schema: dict) -> None:
    """Validate an instance against a JSON schema"""
    try:
        jsonschema.validate(instance=instance, schema=schema)
    except jsonschema.ValidationError as e:
        logger.error(f"{str(e)}")
        raise InvalidFormatException(f"{str(e)}")

def get_agent_schemas(agent_id: str):
    """Get input, output and config schemas for an agent"""
    agent_info = AGENTS.get(agent_id)
    if not agent_info or not agent_info.manifest:
        raise AgentNotFoundException(f"Agent {agent_id} not found")
    
    specs = agent_info.manifest.specs
    return {
        'input': specs.input,
        'output': specs.output,
        'config': specs.config
    }