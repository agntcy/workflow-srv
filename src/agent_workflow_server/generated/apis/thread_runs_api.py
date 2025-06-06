# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from agent_workflow_server.generated.apis.thread_runs_api_base import BaseThreadRunsApi
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
from pydantic import Field, StrictBool, StrictInt, StrictStr, field_validator
from typing import Any, List, Optional
from typing_extensions import Annotated
from agent_workflow_server.generated.models.run_create_stateful import RunCreateStateful
from agent_workflow_server.generated.models.run_output_stream import RunOutputStream
from agent_workflow_server.generated.models.run_stateful import RunStateful
from agent_workflow_server.generated.models.run_wait_response_stateful import RunWaitResponseStateful


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/threads/{thread_id}/runs/{run_id}/cancel",
    responses={
        204: {"description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Cancel Run",
    response_model_by_alias=True,
)
async def cancel_thread_run(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
    wait: Optional[StrictBool] = Query(False, description="", alias="wait"),
    action: Annotated[Optional[StrictStr], Field(description="Action to take when cancelling the run. Possible values are `interrupt` or `rollback`. `interrupt` will simply cancel the run. `rollback` will cancel the run and delete the run and associated checkpoints afterwards.")] = Query(interrupt, description="Action to take when cancelling the run. Possible values are &#x60;interrupt&#x60; or &#x60;rollback&#x60;. &#x60;interrupt&#x60; will simply cancel the run. &#x60;rollback&#x60; will cancel the run and delete the run and associated checkpoints afterwards.", alias="action"),
) -> None:
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().cancel_thread_run(thread_id, run_id, wait, action)


@router.post(
    "/threads/{thread_id}/runs/stream",
    responses={
        200: {"model": RunOutputStream, "description": "Stream of agent results either as &#x60;ValueRunResultUpdate&#x60; objects or &#x60;CustomRunResultUpdate&#x60; objects, according to the specific streaming mode requested. Note that the stream of events is carried using the format specified in SSE spec &#x60;text/event-stream&#x60;"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Create a run on a thread and stream its output",
    response_model_by_alias=True,
)
async def create_and_stream_thread_run_output(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    run_create_stateful: RunCreateStateful = Body(None, description=""),
) -> RunOutputStream:
    """Create a run on a thread and join its output stream. See &#39;GET /runs/{run_id}/stream&#39; for details on the return values."""
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().create_and_stream_thread_run_output(thread_id, run_create_stateful)


@router.post(
    "/threads/{thread_id}/runs/wait",
    responses={
        200: {"model": RunWaitResponseStateful, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Create a run on a thread and block waiting for the result of the run",
    response_model_by_alias=True,
)
async def create_and_wait_for_thread_run_output(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    run_create_stateful: RunCreateStateful = Body(None, description=""),
) -> RunWaitResponseStateful:
    """Create a run on a thread and block waiting for its output. See &#39;GET /runs/{run_id}/wait&#39; for details on the return values."""
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().create_and_wait_for_thread_run_output(thread_id, run_create_stateful)


@router.post(
    "/threads/{thread_id}/runs",
    responses={
        200: {"model": RunStateful, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Create a Background Run on a thread",
    response_model_by_alias=True,
)
async def create_thread_run(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    run_create_stateful: RunCreateStateful = Body(None, description=""),
) -> RunStateful:
    """Create a run on a thread, return the run ID immediately. Don&#39;t wait for the final run output."""
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().create_thread_run(thread_id, run_create_stateful)


@router.delete(
    "/threads/{thread_id}/runs/{run_id}",
    responses={
        204: {"description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Delete Run",
    response_model_by_alias=True,
)
async def delete_thread_run(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
) -> None:
    """Delete a run by ID."""
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().delete_thread_run(thread_id, run_id)


@router.get(
    "/threads/{thread_id}/runs/{run_id}",
    responses={
        200: {"model": RunStateful, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Get Run",
    response_model_by_alias=True,
)
async def get_thread_run(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
) -> RunStateful:
    """Get a run by ID."""
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().get_thread_run(thread_id, run_id)


@router.get(
    "/threads/{thread_id}/runs",
    responses={
        200: {"model": List[RunStateful], "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="List Runs for a thread",
    response_model_by_alias=True,
)
async def list_thread_runs(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    limit: Optional[StrictInt] = Query(10, description="", alias="limit"),
    offset: Optional[StrictInt] = Query(0, description="", alias="offset"),
) -> List[RunStateful]:
    """List runs for a thread."""
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().list_thread_runs(thread_id, limit, offset)


@router.post(
    "/threads/{thread_id}/runs/{run_id}",
    responses={
        200: {"model": RunStateful, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Resume an interrupted Run",
    response_model_by_alias=True,
)
async def resume_thread_run(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
    body: Optional[Any] = Body(None, description=""),
) -> RunStateful:
    """Provide the needed input to a run to resume its execution. Can only be called for runs that are in the interrupted state Schema of the provided input must match with the schema specified in the agent specs under interrupts for the interrupt type the agent generated for this specific interruption."""
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().resume_thread_run(thread_id, run_id, body)


@router.get(
    "/threads/{thread_id}/runs/{run_id}/stream",
    responses={
        200: {"model": RunOutputStream, "description": "Stream of agent results either as &#x60;ValueRunResultUpdate&#x60; objects or &#x60;CustomRunResultUpdate&#x60; objects, according to the specific streaming mode requested. Note that the stream of events is carried using the format specified in SSE spec &#x60;text/event-stream&#x60;"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Stream output from Run",
    response_model_by_alias=True,
)
async def stream_thread_run_output(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
) -> RunOutputStream:
    """Join the output stream of an existing run. See &#39;GET /runs/{run_id}/stream&#39; for details on the return values."""
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().stream_thread_run_output(thread_id, run_id)


@router.get(
    "/threads/{thread_id}/runs/{run_id}/wait",
    responses={
        200: {"model": RunWaitResponseStateful, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Blocks waiting for the result of the run.",
    response_model_by_alias=True,
)
async def wait_for_thread_run_output(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(..., description="The ID of the thread."),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
) -> RunWaitResponseStateful:
    """Blocks waiting for the result of the run. See &#39;GET /runs/{run_id}/wait&#39; for details on the return values."""
    if not BaseThreadRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseThreadRunsApi.subclasses[0]().wait_for_thread_run_output(thread_id, run_id)
