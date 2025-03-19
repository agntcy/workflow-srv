import logging
from fastapi import Depends, HTTPException, Request
import jsonschema

from agent_workflow_server.agents.load import AGENTS
from agent_workflow_server.validation.validation import AgentNotFoundException, InvalidFormatException, UnprocessableContentException, get_agent_schemas, validate_against_schema
from ..generated.models.run_create import RunCreate

logger = logging.getLogger(__name__)

async def validate_run_create(request: Request, run_create: RunCreate) -> RunCreate:
    """Validate RunCreate input against agent's descriptor schema"""
    try:
        schemas = get_agent_schemas(run_create.agent_id)
        
        if run_create.input:
            if not schemas['input']:
                raise UnprocessableContentException("Agent does not define input schema")
            validate_against_schema(run_create.input, schemas['input'])
            
        if run_create.config:
            if not schemas['config']:
                raise UnprocessableContentException("Agent does not define config schema")
            validate_against_schema(run_create.config, schemas['config'])
            
        return run_create
        
    except AgentNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except UnprocessableContentException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except InvalidFormatException as e:
        raise HTTPException(status_code=500, detail=str(e))