# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from pydantic import Field, StrictBool, StrictStr
from typing_extensions import Annotated

from agent_workflow_server.generated.models.run_create_stateless import (
    RunCreateStateless,
)
from agent_workflow_server.generated.models.run_output import (
    RunError,
    RunOutput,
    RunResult,
)
from agent_workflow_server.generated.models.run_output_stream import RunOutputStream
from agent_workflow_server.generated.models.run_search_request import RunSearchRequest
from agent_workflow_server.generated.models.run_stateless import RunStateless
from agent_workflow_server.generated.models.run_wait_response_stateless import (
    RunWaitResponseStateless,
)
from agent_workflow_server.services.runs import Runs
from agent_workflow_server.services.validation import (
    InvalidFormatException,
)
from agent_workflow_server.services.validation import (
    validate_run_create as validate,
)

router = APIRouter()


async def _validate_run_create(
    run_create_stateless: RunCreateStateless,
) -> RunCreateStateless:
    """Validate RunCreate input against agent's descriptor schema"""
    try:
        validate(run_create_stateless)
    except InvalidFormatException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


async def _wait_and_return_run_output(run_id: str) -> RunWaitResponseStateless:
    try:
        run, run_output = await Runs.wait_for_output(run_id)
    except TimeoutError:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except InvalidFormatException as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e)
        )
    if run is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    if run.status == "success" and run_output is not None:
        return RunWaitResponseStateless(
            run=run,
            output=RunOutput(RunResult(type="result", values=run_output)),
        )
    else:
        return RunWaitResponseStateless(
            run=run,
            output=RunOutput(
                RunError(type="error", run_id=run_id, errcode=1, description=run_output)
            ),
        )


@router.post(
    "/runs/{run_id}/cancel",
    responses={
        204: {"description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Cancel Stateless Run",
    response_model_by_alias=True,
)
async def cancel_stateless_run(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
    wait: Optional[StrictBool] = Query(False, description="", alias="wait"),
    action: Annotated[
        Optional[StrictStr],
        Field(
            description="Action to take when cancelling the run. Possible values are `interrupt` or `rollback`. `interrupt` will simply cancel the run. `rollback` will cancel the run and delete the run and associated checkpoints afterwards."
        ),
    ] = Query(
        "interrupt",
        description="Action to take when cancelling the run. Possible values are &#x60;interrupt&#x60; or &#x60;rollback&#x60;. &#x60;interrupt&#x60; will simply cancel the run. &#x60;rollback&#x60; will cancel the run and delete the run and associated checkpoints afterwards.",
        alias="action",
    ),
) -> None:
    raise HTTPException(status_code=500, detail="Not implemented")


@router.post(
    "/runs/stream",
    responses={
        200: {
            "model": RunOutputStream,
            "description": "Stream of agent results either as &#x60;ValueRunResultUpdate&#x60; objects or &#x60;CustomRunResultUpdate&#x60; objects, according to the specific streaming mode requested. Note that the stream of events is carried using the format specified in SSE spec &#x60;text/event-stream&#x60;",
        },
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Create a stateless run and stream its output",
    response_model_by_alias=True,
    dependencies=[Depends(_validate_run_create)],
)
async def create_and_stream_stateless_run_output(
    run_create_stateless: RunCreateStateless = Body(None, description=""),
) -> RunOutputStream:
    """Create a stateless run and join its output stream. See &#39;GET /runs/{run_id}/stream&#39; for details on the return values."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.post(
    "/runs/wait",
    responses={
        200: {"model": RunWaitResponseStateless, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Create a stateless run and wait for its output",
    response_model_by_alias=True,
    dependencies=[Depends(_validate_run_create)],
)
async def create_and_wait_for_stateless_run_output(
    run_create_stateless: RunCreateStateless = Body(None, description=""),
) -> RunWaitResponseStateless:
    """Create a stateless run and wait for its output. See &#39;GET /runs/{run_id}/wait&#39; for details on the return values."""
    new_run = await Runs.put(run_create_stateless)
    return await _wait_and_return_run_output(new_run.run_id)


@router.post(
    "/runs",
    responses={
        200: {"model": RunStateless, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Create a Background stateless Run",
    response_model_by_alias=True,
    dependencies=[Depends(_validate_run_create)],
)
async def create_stateless_run(
    run_create_stateless: RunCreateStateless = Body(None, description=""),
) -> RunStateless:
    """Create a stateless run, return the run ID immediately. Don&#39;t wait for the final run output."""
    return await Runs.put(run_create_stateless)


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
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> None:
    """Delete a stateless run by ID."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.get(
    "/runs/{run_id}",
    responses={
        200: {"model": RunStateless, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Get Run",
    response_model_by_alias=True,
)
async def get_stateless_run(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> RunStateless:
    """Get a stateless run by ID."""
    run = Runs.get(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID {run_id} not found",
        )
    return run


@router.post(
    "/runs/{run_id}",
    responses={
        200: {"model": RunStateless, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Resume an interrupted Run",
    response_model_by_alias=True,
)
async def resume_stateless_run(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
    body: Dict[str, Any] = Body(None, description=""),
) -> RunStateless:
    """Provide the needed input to a run to resume its execution. Can only be called for runs that are in the interrupted state Schema of the provided input must match with the schema specified in the agent specs under interrupts for the interrupt type the agent generated for this specific interruption."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.post(
    "/runs/search",
    responses={
        200: {"model": List[RunStateless], "description": "Success"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Search Stateless Runs",
    response_model_by_alias=True,
)
async def search_stateless_runs(
    run_search_request: RunSearchRequest = Body(None, description=""),
) -> List[RunStateless]:
    """Search for stateless run.  This endpoint also functions as the endpoint to list all stateless Runs."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.get(
    "/runs/{run_id}/stream",
    responses={
        200: {
            "model": RunOutputStream,
            "description": "Stream of agent results either as &#x60;ValueRunResultUpdate&#x60; objects or &#x60;CustomRunResultUpdate&#x60; objects, according to the specific streaming mode requested. Note that the stream of events is carried using the format specified in SSE spec &#x60;text/event-stream&#x60;",
        },
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Stream output from Stateless Run",
    response_model_by_alias=True,
)
async def stream_stateless_run_output(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> RunOutputStream:
    """Join the output stream of an existing run. This endpoint streams output in real-time from a run. Only output produced after this endpoint is called will be streamed."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.get(
    "/runs/{run_id}/wait",
    responses={
        200: {"model": RunWaitResponseStateless, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Stateless Runs"],
    summary="Blocks waiting for the result of the run.",
    response_model_by_alias=True,
)
async def wait_for_stateless_run_output(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> RunWaitResponseStateless:
    """Blocks waiting for the result of the run. The output can be:   * an interrupt, this happens when the agent run status is &#x60;interrupted&#x60;   * the final result of the run, this happens when the agent run status is &#x60;success&#x60;   * an error, this happens when the agent run status is &#x60;error&#x60; or &#x60;timeout&#x60;   This call blocks until the output is available."""
    return await _wait_and_return_run_output(run_id)
