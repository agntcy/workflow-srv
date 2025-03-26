# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from agent_workflow_server.generated.apis.threads_api_base import BaseThreadsApi
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
from pydantic import Field, StrictInt, StrictStr
from typing import Any, List, Optional
from typing_extensions import Annotated
from agent_workflow_server.generated.models.thread import Thread
from agent_workflow_server.generated.models.thread_create import ThreadCreate
from agent_workflow_server.generated.models.thread_patch import ThreadPatch
from agent_workflow_server.generated.models.thread_search_request import ThreadSearchRequest
from agent_workflow_server.generated.models.thread_state import ThreadState


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/threads/{thread_id}/copy",
    responses={
        200: {"model": Thread, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Copy Thread",
    response_model_by_alias=True,
)
async def copy_thread(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
) -> Thread:
    """Create a new thread with a copy of the state and checkpoints from an existing thread."""
    if not BaseThreadsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadsApi.subclasses[0]().copy_thread(thread_id)


@router.post(
    "/threads",
    responses={
        200: {"model": Thread, "description": "Success"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Create an empty Thread",
    response_model_by_alias=True,
)
async def create_thread(
    thread_create: ThreadCreate = Body(None, description=""),
) -> Thread:
    """Create a new thread. """
    if not BaseThreadsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadsApi.subclasses[0]().create_thread(thread_create)


@router.delete(
    "/threads/{thread_id}",
    responses={
        204: {"description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Delete a thread. If the thread contains any pending run, deletion fails.",
    response_model_by_alias=True,
)
async def delete_thread(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
) -> None:
    """Delete a thread."""
    if not BaseThreadsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadsApi.subclasses[0]().delete_thread(thread_id)


@router.get(
    "/threads/{thread_id}",
    responses={
        200: {"model": Thread, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Get Thread",
    response_model_by_alias=True,
)
async def get_thread(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
) -> Thread:
    """Get a thread from its ID. """
    if not BaseThreadsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadsApi.subclasses[0]().get_thread(thread_id)


@router.get(
    "/threads/{thread_id}/history",
    responses={
        200: {"model": List[ThreadState], "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Get Thread History",
    response_model_by_alias=True,
)
async def get_thread_history(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    limit: Optional[StrictInt] = Query(10, description="", alias="limit"),
    before: Optional[StrictStr] = Query(None, description="", alias="before"),
) -> List[ThreadState]:
    """Get all past states for a thread."""
    if not BaseThreadsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadsApi.subclasses[0]().get_thread_history(thread_id, limit, before)


@router.patch(
    "/threads/{thread_id}",
    responses={
        200: {"model": Thread, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Patch Thread",
    response_model_by_alias=True,
)
async def patch_thread(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    thread_patch: ThreadPatch = Body(None, description=""),
) -> Thread:
    """Update a thread."""
    if not BaseThreadsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadsApi.subclasses[0]().patch_thread(thread_id, thread_patch)


@router.post(
    "/threads/search",
    responses={
        200: {"model": List[Thread], "description": "Success"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Search Threads",
    response_model_by_alias=True,
)
async def search_threads(
    thread_search_request: ThreadSearchRequest = Body(None, description=""),
) -> List[Thread]:
    """Search for threads.  This endpoint also functions as the endpoint to list all threads."""
    if not BaseThreadsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadsApi.subclasses[0]().search_threads(thread_search_request)
