# coding: utf-8

from typing import List  # noqa: F401

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    HTTPException,
    Path,
)
from pydantic import Field, StrictStr
from typing_extensions import Annotated

from agent_workflow_server.agents.load import get_agent_info
from agent_workflow_server.generated.models.agent import Agent
from agent_workflow_server.generated.models.agent_acp_descriptor import (
    AgentACPDescriptor,
)
from agent_workflow_server.generated.models.agent_search_request import (
    AgentSearchRequest,
)

router = APIRouter()


@router.get(
    "/agents/{agent_id}/descriptor",
    responses={
        200: {"model": AgentACPDescriptor, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Agents"],
    summary="Get Agent ACP Descriptor from its id",
    response_model_by_alias=True,
)
async def get_acp_descriptor_by_id(
    agent_id: Annotated[StrictStr, Field(description="The ID of the agent.")] = Path(
        ..., description="The ID of the agent."
    ),
) -> AgentACPDescriptor:
    """Get agent ACP descriptor by agent ID."""

    agent = get_agent_info()

    return agent.manifest


@router.get(
    "/agents/{agent_id}",
    responses={
        200: {"model": Agent, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Agents"],
    summary="Get Agent",
    response_model_by_alias=True,
)
async def get_agent_by_id(
    agent_id: Annotated[StrictStr, Field(description="The ID of the agent.")] = Path(
        ..., description="The ID of the agent."
    ),
) -> Agent:
    """Get an agent by ID."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.post(
    "/agents/search",
    responses={
        200: {"model": List[Agent], "description": "Success"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Agents"],
    summary="Search Agents",
    response_model_by_alias=True,
)
async def search_agents(
    agent_search_request: AgentSearchRequest = Body(None, description=""),
) -> List[Agent]:
    """Returns a list of agents matching the criteria provided in the request.  This endpoint also functions as the endpoint to list all agents."""
    raise HTTPException(status_code=500, detail="Not implemented")
