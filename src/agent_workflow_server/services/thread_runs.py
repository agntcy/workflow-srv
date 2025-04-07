from datetime import datetime
import logging
from typing import List
from uuid import uuid4

from agent_workflow_server.generated.models.run_stateful import RunStateful as ApiRunStateful
from agent_workflow_server.generated.models.run_create_stateful import (
    RunCreateStateful as ApiRunCreateStateful,
)
from agent_workflow_server.services.runs import RUNS_QUEUE
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
        "thread_id": run_create.thread_id,
        "status": run_create.status,
        "metadata": run_create.metadata,
        "created_at": curr_time,
        "updated_at": curr_time,
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
        run_id=run["run_id"],
        thread_id=run["thread_id"],
        status=run["status"],
        metadata=run["metadata"],
        created_at=run["created_at"],
        updated_at=run["updated_at"],
    )


class ThreadRuns:
    @staticmethod
    async def get_thread_runs(thread_id: str) -> List[ApiRunStateful]:
        """Get all runs for a given thread ID."""
        # Fetch the thread from the database
        thread = DB.get_thread(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} does not exist.")
            raise Exception("Thread not found")

        # Placeholder for actual implementation
        runs = DB.search_runs({"thread_id": thread_id})
        if runs:
            # Convert each run to its API model representation
            return [_to_api_model(run) for run in runs]
        else:
            logger.warning(f"No runs found for thread ID: {thread_id}")

        return []
    
    @staticmethod
    async def put(run_create: ApiRunCreateStateful) -> ApiRunStateful:
        """Create a new run."""
        # Check if the thread exists
        thread = DB.get_thread(run_create.thread_id)
        if not thread:
            logger.error(f"Thread with ID {run_create.thread_id} does not exist.")
            raise ThreadNotFoundError(
                f"Thread with ID {run_create.thread_id} does not exist."
            )
        
        # Check if the thread has pending runs
        has_pending_runs = Threads.check_pending_runs(run_create.thread_id)
        if has_pending_runs:
            logger.error(f"Thread with ID {run_create.thread_id} has pending runs.")
            raise PendingRunError(
                f"Thread with ID {run_create.thread_id} has pending runs."
            )

        new_run = _make_run(run_create)
        DB.create_run(new_run)
        run_info = RunInfo(
            run_id=new_run["run_id"],
            attempts=0,
        )
        DB.create_run(new_run)
        DB.create_run_info(run_info)

        await RUNS_QUEUE.put(new_run["run_id"])
        
        return _to_api_model(new_run)
    

    
