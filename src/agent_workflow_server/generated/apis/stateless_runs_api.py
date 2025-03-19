# coding: utf-8

from typing import Dict, List  # noqa: F401
import importlib
import pkgutil

from agent_workflow_server.generated.apis.stateless_runs_api_base import BaseStatelessRunsApi
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
from pydantic import Field, StrictBool, StrictStr, field_validator
from typing import Any, List, Optional
from typing_extensions import Annotated
from agent_workflow_server.generated.models.run import Run
from agent_workflow_server.generated.models.run_create_stateless import RunCreateStateless
from agent_workflow_server.generated.models.run_output_stream import RunOutputStream
from agent_workflow_server.generated.models.run_search_request import RunSearchRequest
from agent_workflow_server.generated.models.run_wait_response import RunWaitResponse


router = APIRouter()

ns_pkg = openapi_server.impl
for _, name, _ in pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + "."):
    importlib.import_module(name)


@router.post(
    "/runs/{run_id}/cancel",
    responses={
        204: {"description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Cancel Stateless Run",
    response_model_by_alias=True,
)
async def cancel_stateless_run(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
    wait: Optional[StrictBool] = Query(False, description="", alias="wait"),
    action: Annotated[Optional[StrictStr], Field(description="Action to take when cancelling the run. Possible values are `interrupt` or `rollback`. `interrupt` will simply cancel the run. `rollback` will cancel the run and delete the run and associated checkpoints afterwards.")] = Query(interrupt, description="Action to take when cancelling the run. Possible values are &#x60;interrupt&#x60; or &#x60;rollback&#x60;. &#x60;interrupt&#x60; will simply cancel the run. &#x60;rollback&#x60; will cancel the run and delete the run and associated checkpoints afterwards.", alias="action"),
) -> None:
    if not BaseStatelessRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatelessRunsApi.subclasses[0]().cancel_stateless_run(run_id, wait, action)


@router.post(
    "/runs/stream",
    responses={
        200: {"model": RunOutputStream, "description": "Stream of agent results either as &#x60;ValueRunResultUpdate&#x60; objects or &#x60;CustomRunResultUpdate&#x60; objects, according to the specific streaming mode requested. Note that the stream of events is carried using the format specified in SSE spec &#x60;text/event-stream&#x60;"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Create a stateless run and stream its output",
    response_model_by_alias=True,
)
async def create_and_stream_stateless_run_output(
    run_create_stateless: RunCreateStateless = Body(None, description=""),
) -> RunOutputStream:
    """Create a stateless run and join its output stream. See &#39;GET /runs/{run_id}/stream&#39; for details on the return values."""
    if not BaseStatelessRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatelessRunsApi.subclasses[0]().create_and_stream_stateless_run_output(run_create_stateless)


@router.post(
    "/runs/wait",
    responses={
        200: {"model": RunWaitResponse, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Create a stateless run and wait for its output",
    response_model_by_alias=True,
)
async def create_and_wait_for_stateless_run_output(
    run_create_stateless: RunCreateStateless = Body(None, description=""),
) -> RunWaitResponse:
    """Create a stateless run and wait for its output. See &#39;GET /runs/{run_id}/wait&#39; for details on the return values."""
    if not BaseStatelessRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatelessRunsApi.subclasses[0]().create_and_wait_for_stateless_run_output(run_create_stateless)


@router.post(
    "/runs",
    responses={
        200: {"model": Run, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Create a Background stateless Run",
    response_model_by_alias=True,
)
async def create_stateless_run(
    run_create_stateless: RunCreateStateless = Body(None, description=""),
) -> Run:
    """Create a stateless run, return the run ID immediately. Don&#39;t wait for the final run output."""
    if not BaseStatelessRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatelessRunsApi.subclasses[0]().create_stateless_run(run_create_stateless)


@router.delete(
    "/runs/{run_id}",
    responses={
        204: {"description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Delete Stateless Run",
    response_model_by_alias=True,
)
async def delete_stateless_run(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
) -> None:
    """Delete a stateless run by ID."""
    if not BaseStatelessRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatelessRunsApi.subclasses[0]().delete_stateless_run(run_id)


@router.get(
    "/runs/{run_id}",
    responses={
        200: {"model": Run, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Get Run",
    response_model_by_alias=True,
)
async def get_stateless_run(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
) -> Run:
    """Get a stateless run by ID."""
    if not BaseStatelessRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatelessRunsApi.subclasses[0]().get_stateless_run(run_id)


@router.post(
    "/runs/search",
    responses={
        200: {"model": List[Run], "description": "Success"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Search Stateless Runs",
    response_model_by_alias=True,
)
async def search_stateless_runs(
    run_search_request: RunSearchRequest = Body(None, description=""),
) -> List[Run]:
    """Search for stateless run.  This endpoint also functions as the endpoint to list all stateless Runs."""
    if not BaseStatelessRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatelessRunsApi.subclasses[0]().search_stateless_runs(run_search_request)


@router.get(
    "/runs/{run_id}/stream",
    responses={
        200: {"model": RunOutputStream, "description": "Stream of agent results either as &#x60;ValueRunResultUpdate&#x60; objects or &#x60;CustomRunResultUpdate&#x60; objects, according to the specific streaming mode requested. Note that the stream of events is carried using the format specified in SSE spec &#x60;text/event-stream&#x60;"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Stream output from Stateless Run",
    response_model_by_alias=True,
)
async def stream_stateless_run_output(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
) -> RunOutputStream:
    """Join the output stream of an existing run. This endpoint streams output in real-time from a run. Only output produced after this endpoint is called will be streamed."""
    if not BaseStatelessRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatelessRunsApi.subclasses[0]().stream_stateless_run_output(run_id)


@router.get(
    "/runs/{run_id}/wait",
    responses={
        200: {"model": RunWaitResponse, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Retrieve last output of a run if available",
    response_model_by_alias=True,
)
async def wait_for_stateless_run_output(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(..., description="The ID of the run."),
) -> RunWaitResponse:
    """Retrieve the last output of the run.  The output can be:   * an interrupt, this happens when the agent run status is &#x60;interrupted&#x60;   * the final result of the run, this happens when the agent run status is &#x60;success&#x60;   * an error, this happens when the agent run status is &#x60;error&#x60; or &#x60;timeout&#x60;   This call blocks until the output is available."""
    if not BaseStatelessRunsApi.subclasses:
        raise HTTPException(status_code=500, detail="Not implemented")
    return await BaseStatelessRunsApi.subclasses[0]().wait_for_stateless_run_output(run_id)
