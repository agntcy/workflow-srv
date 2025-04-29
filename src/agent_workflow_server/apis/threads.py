# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import List, Optional

from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Path,
    Query,
    status,
)
from pydantic import Field, StrictInt, StrictStr
from typing_extensions import Annotated

from agent_workflow_server.agents.base import ThreadsNotSupportedError
from agent_workflow_server.generated.models.thread import Thread
from agent_workflow_server.generated.models.thread_create import ThreadCreate
from agent_workflow_server.generated.models.thread_patch import ThreadPatch
from agent_workflow_server.generated.models.thread_search_request import (
    ThreadSearchRequest,
)
from agent_workflow_server.generated.models.thread_state import ThreadState
from agent_workflow_server.services.threads import (
    DuplicatedThreadError,
    PendingRunError,
    Threads,
)

router = APIRouter()


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
) -> Thread:
    """Create a new thread with a copy of the state and checkpoints from an existing thread."""
    try:
        copiedThread = await Threads.copy_thread(thread_id)
    except DuplicatedThreadError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread with ID {thread_id} not found",
        )

    return copiedThread


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
    """Create an empty thread."""
    raiseExistError = True if thread_create.if_exists == "raise" else False
    try:
        newThread = await Threads.create_thread(thread_create, raiseExistError)
    except DuplicatedThreadError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Thread with ID {thread_create.thread_id} already exists",
        )

    return newThread


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
) -> None:
    """Delete a thread."""
    try:
        success = await Threads.delete_thread(thread_id)
        if success is False:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Thread not found")
    except PendingRunError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Thread has pending runs. Cannot delete.",
        )


@router.get(
    "/threads/{thread_id}",
    responses={
        200: {"model": Thread, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Get a previously created Thread",
    response_model_by_alias=True,
)
async def get_thread(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
) -> Thread:
    """Get a thread from its ID."""
    try:
        thread = await Threads.get_thread_by_id(thread_id)
    except ThreadsNotSupportedError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Thread is not supported for this agent.",
        )
    if thread is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Thread not found")

    return thread


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    limit: Optional[StrictInt] = Query(10, description="", alias="limit"),
    before: Optional[StrictStr] = Query(None, description="", alias="before"),
) -> List[ThreadState]:
    """Get all past states for a thread."""

    try:
        thread = await Threads.get_history(thread_id, limit, before)
        if thread is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Thread not found")
    except ThreadsNotSupportedError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Thread is not supported for this agent.",
        )

    return thread


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    thread_patch: ThreadPatch = Body(None, description=""),
) -> Thread:
    """Update a thread."""
    try:
        thread = await Threads.update_thread(thread_id, thread_patch.to_dict())
    except ValueError as e:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to update thread: {e}",
        )

    if thread is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Thread not found")


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
    return await Threads.search(thread_search_request)
