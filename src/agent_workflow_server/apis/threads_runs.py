# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import Any, Dict, List, Optional  # noqa: F401

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
from pydantic import Field, StrictBool, StrictInt, StrictStr
from typing_extensions import Annotated

from agent_workflow_server.agents.base import ThreadsNotSupportedError
from agent_workflow_server.agents.load import get_default_agent
from agent_workflow_server.generated.models.extra_models import TokenModel  # noqa: F401
from agent_workflow_server.generated.models.run_create_stateful import RunCreateStateful
from agent_workflow_server.generated.models.run_error import RunError
from agent_workflow_server.generated.models.run_output import RunOutput
from agent_workflow_server.generated.models.run_output_stream import RunOutputStream
from agent_workflow_server.generated.models.run_result import RunResult
from agent_workflow_server.generated.models.run_stateful import RunStateful
from agent_workflow_server.generated.models.run_wait_response_stateful import (
    RunWaitResponseStateful,
)
from agent_workflow_server.services.thread_runs import ThreadNotFoundError, ThreadRuns
from agent_workflow_server.services.threads import PendingRunError, Threads
from agent_workflow_server.services.validation import (
    InvalidFormatException,
)
from agent_workflow_server.services.validation import (
    validate_run_create as validate,
)

from ..utils.tools import make_serializable

router = APIRouter()


async def _validate_run_create(
    run_create_stateful: RunCreateStateful,
) -> RunCreateStateful:
    """Validate RunCreate input against agent's descriptor schema"""
    try:
        if run_create_stateful.agent_id is None:
            """Pre-process the RunCreateStateless object to set the agent_id if not provided."""
            run_create_stateful.agent_id = get_default_agent().agent_id

        validate(run_create_stateful)
    except InvalidFormatException as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


async def _wait_and_return_run_output(run_id: str) -> RunWaitResponseStateful:
    try:
        run, run_output = await ThreadRuns.wait_for_output(run_id)
    except TimeoutError:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except InvalidFormatException as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e)
        )
    if run is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    if run.status == "success" and run_output is not None:
        return RunWaitResponseStateful(
            run=run,
            output=RunOutput(
                RunResult(type="result", values=make_serializable(run_output))
            ),
        )
    else:
        return RunWaitResponseStateful(
            run=run,
            output=RunOutput(
                RunError(type="error", run_id=run_id, errcode=1, description=run_output)
            ),
        )


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
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
    "/threads/{thread_id}/runs/stream",
    responses={
        200: {
            "model": RunOutputStream,
            "description": "Stream of agent results either as &#x60;ValueRunResultUpdate&#x60; objects or &#x60;CustomRunResultUpdate&#x60; objects, according to the specific streaming mode requested. Note that the stream of events is carried using the format specified in SSE spec &#x60;text/event-stream&#x60;",
        },
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Create a run on a thread and stream its output",
    response_model_by_alias=True,
    dependencies=[Depends(_validate_run_create)],
)
async def create_and_stream_thread_run_output(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    run_create_stateful: RunCreateStateful = Body(None, description=""),
) -> RunOutputStream:
    """Create a run on a thread and join its output stream. See &#39;GET /runs/{run_id}/stream&#39; for details on the return values."""
    raise HTTPException(status_code=500, detail="Not implemented")


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
    dependencies=[Depends(_validate_run_create)],
)
async def create_and_wait_for_thread_run_output(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    run_create_stateful: RunCreateStateful = Body(None, description=""),
) -> RunWaitResponseStateful:
    """Create a run on a thread and block waiting for its output. See &#39;GET /runs/{run_id}/wait&#39; for details on the return values."""
    try:
        new_run = await ThreadRuns.put(run_create_stateful, thread_id)
    except ThreadNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except PendingRunError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))

    return await _wait_and_return_run_output(new_run.run_id)


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
    dependencies=[Depends(_validate_run_create)],
)
async def create_thread_run(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    run_create_stateful: RunCreateStateful = Body(None, description=""),
) -> RunStateful:
    """Create a run on a thread, return the run ID immediately. Don&#39;t wait for the final run output."""
    try:
        return ThreadRuns.put(run_create_stateful, thread_id)
    except ThreadNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except PendingRunError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> None:
    """Delete a run by ID."""
    try:
        await ThreadRuns.delete(thread_id, run_id)
    except ThreadNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> RunStateful:
    """Get a run by ID."""

    try:
        run = await ThreadRuns.get_thread_run_by_ids(thread_id, run_id)
    except ThreadNotFoundError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Run not found")

    return run


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    limit: Optional[StrictInt] = Query(10, description="", alias="limit"),
    offset: Optional[StrictInt] = Query(0, description="", alias="offset"),
) -> List[RunStateful]:
    """List runs for a thread."""
    try:
        return await ThreadRuns.get_thread_runs(thread_id)
    except Exception as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
    body: Optional[Any] = Body(None, description=""),
) -> RunStateful:
    """Provide the needed input to a run to resume its execution. Can only be called for runs that are in the interrupted state Schema of the provided input must match with the schema specified in the agent specs under interrupts for the interrupt type the agent generated for this specific interruption."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.get(
    "/threads/{thread_id}/runs/{run_id}/stream",
    responses={
        200: {
            "model": RunOutputStream,
            "description": "Stream of agent results either as &#x60;ValueRunResultUpdate&#x60; objects or &#x60;CustomRunResultUpdate&#x60; objects, according to the specific streaming mode requested. Note that the stream of events is carried using the format specified in SSE spec &#x60;text/event-stream&#x60;",
        },
        404: {"model": str, "description": "Not Found"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Thread Runs"],
    summary="Stream output from Run",
    response_model_by_alias=True,
)
async def stream_thread_run_output(
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> RunOutputStream:
    """Join the output stream of an existing run. See &#39;GET /runs/{run_id}/stream&#39; for details on the return values."""
    raise HTTPException(status_code=500, detail="Not implemented")


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
    thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")] = Path(
        ..., description="The ID of the thread."
    ),
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> RunWaitResponseStateful:
    """Blocks waiting for the result of the run. See &#39;GET /runs/{run_id}/wait&#39; for details on the return values."""
    try:
        thread = await Threads.get_thread_by_id(thread_id)
    except ThreadsNotSupportedError:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Thread is not supported for this agent.",
        )
    if thread is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Thread not found")

    # TODO check if given thread has the give run

    return await _wait_and_return_run_output(run_id)
