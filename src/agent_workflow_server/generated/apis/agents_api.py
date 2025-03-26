# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from agent_workflow_server.generated.apis.agents_api_base import BaseAgentsApi
import openapi_server.impl

from fastapi import (  # noqa: F401
    APIRouter,
    Body,
    Cookie,
    Depends,
    Form,
    Header,
    HTTPException,
    Path,
    Query,
    Response,
    Security,
    status,
)

from agent_workflow_server.generated.models.extra_models import TokenModel  # noqa: F401
from pydantic import Field, StrictStr
from typing import List
from typing_extensions import Annotated
from agent_workflow_server.generated.models.agent import Agent
from agent_workflow_server.generated.models.agent_acp_descriptor import AgentACPDescriptor
from agent_workflow_server.generated.models.agent_search_request import AgentSearchRequest


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


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
    agent_id: Annotated[StrictStr, Field(description="The ID of the agent.")] = Path(..., description="The ID of the agent."),
) -> AgentACPDescriptor:
    """Get agent ACP descriptor by agent ID."""
    if not BaseAgentsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAgentsApi.subclasses[0]().get_acp_descriptor_by_id(agent_id)


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
    agent_id: Annotated[StrictStr, Field(description="The ID of the agent.")] = Path(..., description="The ID of the agent."),
) -> Agent:
    """Get an agent by ID."""
    if not BaseAgentsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAgentsApi.subclasses[0]().get_agent_by_id(agent_id)


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
    if not BaseAgentsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseAgentsApi.subclasses[0]().search_agents(agent_search_request)
