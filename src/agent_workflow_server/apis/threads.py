# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import List

from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Path,
)
from pydantic import Field, StrictStr
from typing_extensions import Annotated

from agent_workflow_server.generated.models.run import Run
from agent_workflow_server.generated.models.thread import Thread
from agent_workflow_server.generated.models.thread_create import ThreadCreate
from agent_workflow_server.generated.models.thread_search_request import (
    ThreadSearchRequest,
)

router = APIRouter()


@router.post(
    "/threads",
    responses={
        200: {"model": Thread, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
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
    """Create an empty thread. This is useful to associate metadata to a thread."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.delete(
    "/threads/{thread_id}",
    responses={
        200: {"model": Thread, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
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
) -> Thread:
    """Delete a thread."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.get(
    "/runs/{run_id}/threadstate",
    responses={
        200: {"model": object, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Retrieve the thread state at the end of the run",
    response_model_by_alias=True,
)
async def get_run_threadstate(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> object:
    """This call can be used only for agents that support thread, i.e. for Runs that specify a thread ID. It can be called only on runs that are in &#x60;success&#x60; status. It returns the thread state at the end of the Run. Can be used to reconstruct the evolution of the thread state in its history."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.get(
    "/threads/{thread_id}",
    responses={
        200: {"model": Thread, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
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
    raise HTTPException(status_code=500, detail="Not implemented")


@router.get(
    "/threads/{thread_id}/history",
    responses={
        200: {"model": List[Run], "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Retrieve the list of runs and associated state at the end of each run.",
    response_model_by_alias=True,
)
async def get_thread_history(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
) -> List[Run]:
    """Retrieve ordered list of runs for this thread in chronological order."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.get(
    "/threads/{thread_id}/state",
    responses={
        200: {"model": object, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Threads"],
    summary="Retrieve the current state associated with the thread",
    response_model_by_alias=True,
)
async def get_thread_state(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
) -> object:
    """Retrieve the the current state associated with the thread"""
    raise HTTPException(status_code=500, detail="Not implemented")


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
    raise HTTPException(status_code=500, detail="Not implemented")
