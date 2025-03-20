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
from pydantic import Field, StrictStr
from typing_extensions import Annotated

from agent_workflow_server.apis.depends import validate_run_create
from agent_workflow_server.generated.models.run import Run
from agent_workflow_server.generated.models.run_create import RunCreate
from agent_workflow_server.generated.models.run_output import (
    RunError,
    RunOutput,
    RunResult,
)
from agent_workflow_server.generated.models.run_output_stream import RunOutputStream
from agent_workflow_server.generated.models.run_search_request import RunSearchRequest
from agent_workflow_server.services.runs import Runs
from agent_workflow_server.services.validation import InvalidFormatException

router = APIRouter()


@router.post(
    "/runs",
    responses={
        200: {"model": Run, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Runs"],
    summary="Create Background Run",
    response_model_by_alias=True,
    dependencies=[Depends(validate_run_create)],
)
async def create_run(
    run_create: RunCreate = Body(None, description=""),
) -> Run:
    """Create a run, return the run descriptor immediately. Don&#39;t wait for the final run output."""
    return await Runs.put(run_create)


@router.delete(
    "/runs/{run_id}",
    responses={
        200: {"model": Run, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Runs"],
    summary="Delete a run. If running, cancel and then delete.",
    response_model_by_alias=True,
)
async def delete_run(
    run_id: Annotated[StrictStr, Field(description="The ID of the agent.")] = Path(
        ..., description="The ID of the agent."
    ),
) -> Run:
    """Cancel a run."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.get(
    "/runs/{run_id}",
    responses={
        200: {"model": Run, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Runs"],
    summary="Get a previously created Run",
    response_model_by_alias=True,
)
async def get_run(
    run_id: Annotated[StrictStr, Field(description="The ID of the agent.")] = Path(
        ..., description="The ID of the agent."
    ),
) -> Run:
    """Get a run from its ID. Don&#39;t wait for the final run output."""
    run = Runs.get(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run with ID {run_id} not found",
        )
    return run


@router.get(
    "/runs/{run_id}/output",
    responses={
        204: {"description": "No Output Available"},
        200: {"model": RunResult, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Runs"],
    summary="Retrieve last output of a run if available",
    response_model_by_alias=True,
)
async def get_run_output(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
    block_timeout: Optional[int] = Query(None, description="", alias="block_timeout"),
) -> RunOutput:
    """Retrieve the last output of the run.  The output can be:   * an interrupt, this happens when the agent run status is &#x60;interrupted&#x60;   * the final result of the run, this happens when the agent run status is &#x60;success&#x60;   * an error, this happens when the agent run status is &#x60;error&#x60; or &#x60;timeout&#x60;   If the block timeout is provided and the current run status is &#x60;pending&#x60;, this call blocks until the state changes or the timeout expires.  If no timeout is provided or the timeout has expired and  run status is &#x60;pending&#x60;, this call returns &#x60;204&#x60; with no content."""
    try:
        run, run_output = await Runs.wait_for_output(run_id, block_timeout)
    except TimeoutError:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except InvalidFormatException as e:
        return Response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e)
        )
    if run is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)
    if run.status == "success" and run_output is not None:
        return RunOutput(
            RunResult(
                type="result", run_id=run_id, status=run.status, result=run_output
            )
        )
    else:
        return RunOutput(
            RunError(type="error", run_id=run_id, errcode=1, description=run_output)
        )


@router.get(
    "/runs/{run_id}/stream",
    responses={
        200: {
            "model": RunOutputStream,
            "description": "Stream of agent results either as &#x60;RunResult&#x60; objects or custom objects, according to the specific streaming mode requested. Note that the stream of events is carried using the format specified in SSE spec &#x60;text/event-stream&#x60;",
        },
        204: {"description": "No Output Available"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Runs"],
    summary="Stream the run output",
    response_model_by_alias=True,
)
async def get_run_stream(
    run_id: Annotated[StrictStr, Field(description="The ID of the run.")] = Path(
        ..., description="The ID of the run."
    ),
) -> RunOutputStream:
    """Send a stream of events using Server-sent events (SEE). See &lt;https://html.spec.whatwg.org/multipage/server-sent-events.html&gt; for details."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.post(
    "/runs/{run_id}",
    responses={
        200: {"model": Run, "description": "Success"},
        404: {"model": str, "description": "Not Found"},
        409: {"model": str, "description": "Conflict"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Runs"],
    summary="Resume an interrupted Run",
    response_model_by_alias=True,
)
async def resume_run(
    run_id: Annotated[StrictStr, Field(description="The ID of the agent.")] = Path(
        ..., description="The ID of the agent."
    ),
    body: Dict[str, Any] = Body(None, description=""),
) -> Run:
    """Provide the needed input to a run to resume its execution. Can only be called for runs that are in the interrupted state Schema of the provided input must match with the schema specified in the agent specs under interrupts for the interrupt type the agent generated for this specific interruption."""
    raise HTTPException(status_code=500, detail="Not implemented")


@router.post(
    "/runs/search",
    responses={
        200: {"model": List[Run], "description": "Success"},
        422: {"model": str, "description": "Validation Error"},
    },
    tags=["Runs"],
    summary="Search Runs",
    response_model_by_alias=True,
)
async def search_runs(
    run_search_request: RunSearchRequest = Body(None, description=""),
) -> List[Run]:
    """Search for runs.  This endpoint also functions as the endpoint to list all runs."""
    raise HTTPException(status_code=500, detail="Not implemented")
