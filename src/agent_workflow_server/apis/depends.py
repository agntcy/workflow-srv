from fastapi import HTTPException, status

from agent_workflow_server.generated.models.run_create import RunCreate
from agent_workflow_server.services.validation import (
    InvalidFormatException,
)
from agent_workflow_server.services.validation import (
    validate_run_create as validate,
)


async def validate_run_create(run_create: RunCreate) -> RunCreate:
    """Validate RunCreate input against agent's descriptor schema"""
    try:
        validate(run_create)
    except InvalidFormatException:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid input",
        )
