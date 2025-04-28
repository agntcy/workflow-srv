# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from agent_workflow_server.generated.models.run_create_stateful import (
    RunCreateStateful as ApiRunCreateStateful,
)
from agent_workflow_server.generated.models.run_stateful import (
    RunStateful as ApiRunStateful,
)
from agent_workflow_server.services.runs import RUNS_QUEUE, cvs_pending_run
from agent_workflow_server.services.threads import PendingRunError, Threads
from agent_workflow_server.storage.models import Run, RunInfo
from agent_workflow_server.storage.storage import DB

logger = logging.getLogger(__name__)


class ThreadNotFoundError(Exception):
    """Exception raised when a thread is not found in the database."""

    pass


def _make_run(run_create: ApiRunCreateStateful) -> Run:
    """
    Convert a RunCreate API model to a Run DB model.

    Args:
        run_create (RunCreate): The API model for creating a run.

    Returns:
        Run: The service model representation of the run.
    """
    curr_time = datetime.now()

    return {
        "run_id": str(uuid4()),
        "metadata": run_create.metadata,
        "agent_id": run_create.agent_id,
        "created_at": curr_time,
        "updated_at": curr_time,
        "input": run_create.input,
        "config": run_create.config.model_dump() if run_create.config else None,
        "status": "pending",
    }


def _to_api_model(run: Run) -> ApiRunStateful:
    """
    Convert a Run service model to a Run API model.

    Args:
        run (Run): The service model representation of a run.

    Returns:
        RunStateful: The API model representation of the run.
    """
    return ApiRunStateful(
        creation=ApiRunCreateStateful(
            agent_id=run["agent_id"],
            thread_id=run["thread_id"],
            input=run["input"],
            metadata=run["metadata"],
            config=run["config"],
        ),
        run_id=run["run_id"],
        agent_id=run["agent_id"],
        thread_id=run["thread_id"],
        status=run["status"],
        metadata=run["metadata"],
        created_at=run["created_at"],
        updated_at=run["updated_at"],
    )


class ThreadRuns:
    @staticmethod
    async def get_thread_run_by_ids(
        thread_id: str, run_id: str
    ) -> Optional[ApiRunStateful]:
        """Get a run by thread ID and run ID."""
        # Fetch the thread from the database
        thread = DB.get_thread(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} does not exist.")
            raise ThreadNotFoundError("Thread not found")

        # Fetch the run from the database
        run = DB.get_run(run_id)
        if not run:
            logger.error(f"Run with ID {run_id} does not exist.")
            return None

        if run["thread_id"] != thread_id:
            logger.error(f"Run with ID {run_id} does not belong to thread {thread_id}.")
            raise ValueError(
                f"Run with ID {run_id} does not belong to thread {thread_id}."
            )
        return _to_api_model(run)

    @staticmethod
    async def get_thread_runs(thread_id: str) -> List[ApiRunStateful]:
        """Get all runs for a given thread ID."""
        # Fetch the thread from the database
        thread = DB.get_thread(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} does not exist.")
            raise ThreadNotFoundError("Thread not found")

        # Placeholder for actual implementation
        runs = DB.search_run({"thread_id": thread_id})
        if runs:
            # Convert each run to its API model representation
            return [_to_api_model(run) for run in runs]
        else:
            logger.warning(f"No runs found for thread ID: {thread_id}")

        return []

    @staticmethod
    async def put(run_create: ApiRunCreateStateful, thread_id: str) -> ApiRunStateful:
        """Create a new run."""
        # Check if the thread exists
        thread = await Threads.get_thread_by_id(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} does not exist.")
            raise ThreadNotFoundError(f"Thread with ID {thread_id} does not exist.")

        # Check if the thread has pending runs
        has_pending_runs = await Threads.check_pending_runs(thread_id)
        if has_pending_runs:
            logger.error(f"Thread with ID {thread_id} has pending runs.")
            raise PendingRunError(f"Thread with ID {thread_id} has pending runs.")

        new_run = _make_run(run_create)
        run_info = RunInfo(
            run_id=new_run["run_id"],
            queued_at=datetime.now(),
            attempts=0,
        )
        new_run["thread_id"] = thread_id
        DB.create_run(new_run)
        DB.create_run_info(run_info)

        await RUNS_QUEUE.put(new_run["run_id"])

        return _to_api_model(new_run)

    @staticmethod
    async def wait_for_output(run_id: str, timeout: float = None):
        run = DB.get_run(run_id)

        if run is None:
            return None, None

        if run["status"] != "pending":
            # If the run is already completed, return the stored output immediately
            return _to_api_model(run), DB.get_run_output(run_id)

        # TODO: handle removing cvs when run is completed and there are no more subscribers
        try:
            async with cvs_pending_run[run_id]:
                await asyncio.wait_for(
                    cvs_pending_run[run_id].wait_for(
                        lambda: DB.get_run_status(run_id) != "pending"
                    ),
                    timeout=timeout,
                )
                run = DB.get_run(run_id)
                return _to_api_model(run), DB.get_run_output(run_id)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout reached while waiting for run {run_id}")
            raise TimeoutError

        return None, None

    @staticmethod
    async def delete(thread_id: str, run_id: str):
        """Delete a run by thread ID and run ID."""
        # Fetch the thread from the database
        thread = DB.get_thread(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} does not exist.")
            raise ThreadNotFoundError("Thread not found")

        # Fetch the run from the database
        run = DB.get_run(run_id)
        if not run:
            logger.error(f"Run with ID {run_id} does not exist.")
            return None

        if run["thread_id"] != thread_id:
            logger.error(f"Run with ID {run_id} does not belong to thread {thread_id}.")
            raise ValueError(
                f"Run with ID {run_id} does not belong to thread {thread_id}."
            )

        # Delete the run from the database
        DB.delete_run(run_id)
