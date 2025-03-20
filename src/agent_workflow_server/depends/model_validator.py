import logging
from fastapi import Depends, HTTPException, Request
import jsonschema

from agent_workflow_server.agents.load import AGENTS
from agent_workflow_server.validation.validation import (
    InvalidFormatException,
    get_agent_schemas,
    validate_against_schema,
)
from ..generated.models.run_create import RunCreate

logger = logging.getLogger(__name__)


async def validate_run_create(request: Request, run_create: RunCreate) -> RunCreate:
    """Validate RunCreate input against agent's descriptor schema"""
    try:
        schemas = get_agent_schemas(run_create.agent_id)

        if run_create.input:
            validate_against_schema(run_create.input, schemas["input"])

        if run_create.config:
            validate_against_schema(run_create.config, schemas["config"])

        return run_create

    except InvalidFormatException as e:
        raise HTTPException(status_code=500, detail=str(e))
