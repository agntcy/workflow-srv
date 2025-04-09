# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import List  # noqa: F401

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    HTTPException,
    Path,
    Request,
    Response,
)
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from pydantic import Field, StrictStr
from typing_extensions import Annotated

from agent_workflow_server.agents.load import (
    get_agent,
    get_agent_info,
    get_agent_openapi_schema,
    search_for_agents,
)
from agent_workflow_server.generated.models.agent import Agent
from agent_workflow_server.generated.models.agent_acp_descriptor import (
    AgentACPDescriptor,
)
from agent_workflow_server.generated.models.agent_search_request import (
    AgentSearchRequest,
)

router = APIRouter()
public_router = APIRouter()


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

    try:
        agent_info = get_agent_info(agent_id)
        return agent_info.acp_descriptor
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/agents/{agent_id}",
    responses={
        200: {"model": Agent, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
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

    try:
        agent = get_agent(agent_id)
        return agent
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


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

    try:
        agents = search_for_agents(agent_search_request)
        return agents
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@public_router.get(
    "/agents/{agent_id}/openapi",
    responses={
        200: {
            "content": {"application/json": {"schema": {"type": "object"}}},
            "description": "Success",
        },
        404: {"model": str, "description": "Not Found"},
    },
    tags=["Agents"],
    summary="Get agent-specific OpenAPI",
    response_model_by_alias=True,
)
async def get_agent_openapi(
    agent_id: Annotated[StrictStr, Field(description="The ID of the agent.")] = Path(
        ..., description="The ID of the agent."
    ),
) -> Response:
    """Get the OpenAPI schema for an agent by ID."""

    try:
        openapi = get_agent_openapi_schema(agent_id)
        return Response(content=openapi, media_type="application/json")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@public_router.get(
    "/agents/{agent_id}/docs",
    responses={
        200: {
            "content": {"text/html": {}},
            "description": "Success",
        },
        404: {"model": str, "description": "Not Found"},
    },
    tags=["Agents"],
    summary="Get Agent specific Swagger UI",
)
async def get_agent_docs(
    request: Request,
    agent_id: Annotated[StrictStr, Field(description="The ID of the agent.")] = Path(
        ...,
        description="The ID of the agent.",
    ),
) -> HTMLResponse:
    """Get the Swagger UI documentation for an agent by ID."""
    return get_swagger_ui_html(
        openapi_url=request.url_for("get_agent_openapi", agent_id=agent_id),
        title="Agent API Documentation",
    )
