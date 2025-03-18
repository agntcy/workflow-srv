import logging
from fastapi import Depends, HTTPException, Request
import jsonschema

from agent_workflow_server.agents.load import AGENTS
from ..generated.models.run_create import RunCreate

logger = logging.getLogger(__name__)

async def validate_run_create(request: Request, run_create: RunCreate) -> RunCreate:
    """Validate RunCreate input against agent's descriptor schema"""
    # Get the agent descriptor from AGENTS global
    logger.debug(f"Validating run_create input")
    agent_id = run_create.agent_id
    agent_info = AGENTS.get(agent_id)
    if not agent_info or not agent_info.manifest:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # Validate input if present
    input_schema = agent_info.manifest.specs.input
    if not input_schema:
        raise HTTPException(status_code=422, detail="Agent does not define input schema")

    if run_create.input:
        try:
            jsonschema.validate(instance=run_create.input, schema=input_schema)
        except jsonschema.ValidationError as e:
            raise HTTPException(status_code=422, detail=str(e))

    # Validate config if present
    config_schema = agent_info.manifest.specs.config
    if run_create.config:
        if not config_schema:
            raise HTTPException(status_code=422, detail="Agent does not define config schema")
        try:
            jsonschema.validate(instance=run_create.config, schema=config_schema)
        except jsonschema.ValidationError as e:
            raise HTTPException(status_code=422, detail=f"Invalid config: {str(e)}")

    return run_create