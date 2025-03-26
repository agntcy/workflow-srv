# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictBool, StrictStr, field_validator
from typing import Any, Dict, List, Optional
from typing_extensions import Annotated
from agent_workflow_server.generated.models.run_create_stateless import RunCreateStateless
from agent_workflow_server.generated.models.run_output_stream import RunOutputStream
from agent_workflow_server.generated.models.run_search_request import RunSearchRequest
from agent_workflow_server.generated.models.run_stateless import RunStateless
from agent_workflow_server.generated.models.run_wait_response_stateless import RunWaitResponseStateless


class BaseStatelessRunsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseStatelessRunsApi.subclasses = BaseStatelessRunsApi.subclasses + (cls,)
    async def cancel_stateless_run(
        self,
        run_id: Annotated[StrictStr, Field(description="The ID of the run.")],
        wait: Optional[StrictBool],
        action: Annotated[Optional[StrictStr], Field(description="Action to take when cancelling the run. Possible values are `interrupt` or `rollback`. `interrupt` will simply cancel the run. `rollback` will cancel the run and delete the run and associated checkpoints afterwards.")],
    ) -> None:
        ...


    async def create_and_stream_stateless_run_output(
        self,
        run_create_stateless: RunCreateStateless,
    ) -> RunOutputStream:
        """Create a stateless run and join its output stream. See &#39;GET /runs/{run_id}/stream&#39; for details on the return values."""
        ...


    async def create_and_wait_for_stateless_run_output(
        self,
        run_create_stateless: RunCreateStateless,
    ) -> RunWaitResponseStateless:
        """Create a stateless run and wait for its output. See &#39;GET /runs/{run_id}/wait&#39; for details on the return values."""
        ...


    async def create_stateless_run(
        self,
        run_create_stateless: RunCreateStateless,
    ) -> RunStateless:
        """Create a stateless run, return the run ID immediately. Don&#39;t wait for the final run output."""
        ...


    async def delete_stateless_run(
        self,
        run_id: Annotated[StrictStr, Field(description="The ID of the run.")],
    ) -> None:
        """Delete a stateless run by ID."""
        ...


    async def get_stateless_run(
        self,
        run_id: Annotated[StrictStr, Field(description="The ID of the run.")],
    ) -> RunStateless:
        """Get a stateless run by ID."""
        ...


    async def resume_stateless_run(
        self,
        run_id: Annotated[StrictStr, Field(description="The ID of the run.")],
        body: Dict[str, Any],
    ) -> RunStateless:
        """Provide the needed input to a run to resume its execution. Can only be called for runs that are in the interrupted state Schema of the provided input must match with the schema specified in the agent specs under interrupts for the interrupt type the agent generated for this specific interruption."""
        ...


    async def search_stateless_runs(
        self,
        run_search_request: RunSearchRequest,
    ) -> List[RunStateless]:
        """Search for stateless run.  This endpoint also functions as the endpoint to list all stateless Runs."""
        ...


    async def stream_stateless_run_output(
        self,
        run_id: Annotated[StrictStr, Field(description="The ID of the run.")],
    ) -> RunOutputStream:
        """Join the output stream of an existing run. This endpoint streams output in real-time from a run. Only output produced after this endpoint is called will be streamed."""
        ...


    async def wait_for_stateless_run_output(
        self,
        run_id: Annotated[StrictStr, Field(description="The ID of the run.")],
    ) -> RunWaitResponseStateless:
        """Blocks waiting for the result of the run. The output can be:   * an interrupt, this happens when the agent run status is &#x60;interrupted&#x60;   * the final result of the run, this happens when the agent run status is &#x60;success&#x60;   * an error, this happens when the agent run status is &#x60;error&#x60; or &#x60;timeout&#x60;   This call blocks until the output is available."""
        ...
