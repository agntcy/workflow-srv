import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict
from uuid import uuid4

from agent_workflow_server.agents.load import AGENTS
from agent_workflow_server.generated.models.thread import (
    Thread as ApiThread,
)
from agent_workflow_server.generated.models.thread_checkpoint import (
    ThreadCheckpoint as ApiThreadCheckpoint,
)
from agent_workflow_server.generated.models.thread_create import ThreadCreate
from agent_workflow_server.generated.models.thread_state import (
    ThreadState as ApiThreadState,
)
from agent_workflow_server.services.thread_state import ThreadState
from agent_workflow_server.storage.models import Thread
from agent_workflow_server.storage.storage import DB

logger = logging.getLogger(__name__)


def _make_thread(thread_create: ThreadCreate) -> Thread:
    """
    Convert a ThreadCreate API model to a Thread DB model.

    Args:
        thread_create (ThreadCreate): The API model for creating a thread.

    Returns:
        Thread: The service model representation of the thread.
    """
    curr_time = datetime.now()

    return {
        "thread_id": thread_create.thread_id or str(uuid4()),
        "metadata": thread_create.metadata,
        "created_at": curr_time,
        "updated_at": curr_time,
    }


def _to_api_model(thread: Thread, state: Optional[ThreadState] = None) -> ApiThread:
    """
    Convert a Thread service model to a Thread API model.

    Args:
        thread (Thread): The service model representation of a thread.
        state (Optional[ThreadState]): The optional thread state. Defaults to None.

    Returns:
        Thread: The API model representation of the thread.
    """

    values = None
    if state is not None and len(state) > 0:
        values = state["values"]

    return ApiThread(
        thread_id=thread["thread_id"],
        metadata=thread["metadata"],
        status=thread["status"],
        created_at=thread["created_at"],
        updated_at=thread["updated_at"],
        values=values,
    )


class DuplicatedThreadError(Exception):
    """Exception raised when a thread with the same ID already exists."""


class PendingRunError(Exception):
    """Exception raised when a thread has pending runs."""


class Threads:
    @staticmethod
    async def check_pending_runs(thread_id: str) -> bool:
        """Check if a thread has pending runs"""
        runs = DB.search_run({"thread_id": thread_id, "status": "pending"})
        if runs:
            return True
        return False

    @staticmethod
    async def get_thread_by_id(thread_id: str) -> Optional[ApiThread]:
        """Return a thread by ID"""

        if thread_id not in DB._threads:
            return None
        thread = DB.get_thread(thread_id)

        ## TODO : Update this for multi agent support
        agent_info = next(iter(AGENTS.values()))
        agent = agent_info.agent

        state = await agent.get_agent_state(thread_id)

        return _to_api_model(thread, state)

    @staticmethod
    async def create_thread(
        threadCreate: ThreadCreate, raiseExistError: False
    ) -> ApiThread:
        """Create a new thread"""
        ## if raiseExistError is True and thread already exists, raise error
        if raiseExistError and DB.get_thread(threadCreate.thread_id) is not None:
            raise DuplicatedThreadError(
                f"Thread with ID {threadCreate.thread_id} already exists"
            )

        ## Create new thread. If Value error raised (thread with given ID exists) return existing thread
        try:
            threadModel = _make_thread(threadCreate)
            ## TODO proper status handling
            threadModel["status"] = "idle"
            newThread = DB.create_thread(threadModel)
        except ValueError:
            return _to_api_model(DB.get_thread(threadCreate.thread_id))

        return _to_api_model(newThread)

    @staticmethod
    async def copy_thread(thread_id: str) -> Optional[ApiThread]:
        """Copy a thread"""
        thread = DB.get_thread(thread_id)
        if thread is None:
            return None

        # Create a new thread with the same metadata and status
        new_thread = Thread(
            thread_id=str(uuid4()),  # Generate a new unique ID
            metadata=thread["metadata"],
            status=thread["status"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        # Save the new thread to the database
        copiedThread = DB.create_thread(new_thread)

        return _to_api_model(copiedThread)

    @staticmethod
    async def list_threads() -> list[ApiThread]:
        """List all threads"""
        threads = DB.list_threads()
        return [_to_api_model(thread) for thread in threads]

    @staticmethod
    async def update_thread(thread_id: str, updates: dict) -> Optional[ApiThread]:
        """Update a thread and state"""

        # Fetch the thread from the database
        thread = DB.get_thread(thread_id)
        if not thread:
            logger.error(f"Thread with ID {thread_id} does not exist.")
            return None

        ## TODO: Other values comes from
        processedUpdates = {
            "metadata": updates.get("metadata", thread["metadata"]),
        }

        # Update the thread in the database
        updated_thread = DB.update_thread(thread_id, processedUpdates)
        if not updated_thread:
            logger.error(f"Failed to update thread with ID {thread_id}.")
            return None

        ## TODO: Add await agent.update_agent_state(thread_id, state) call if we want to update inner state as well

        # Fetch the updated thread from the database and its state from the agent
        return await Threads.get_thread_by_id(thread_id)

    @staticmethod
    async def search(filters: dict) -> list[ApiThread]:
        """Search for threads based on filters"""
        threads = DB.search_thread(filters)
        return [_to_api_model(thread) for thread in threads]

    @staticmethod
    async def get_history(
        thread_id: str, limit: int, before: int
    ) -> Optional[List[ApiThreadState]]:
        """Get the history of a thread"""
        ## TODO : Update this for multi agent support
        agent_info = next(iter(AGENTS.values()))
        agent = agent_info.agent

        history = await agent.get_history(thread_id, limit, before)

        # Convert the history to the API model
        api_history = [
            ApiThreadState(
                checkpoint=ApiThreadCheckpoint(checkpoint_id=state["checkpoint_id"]),
                values=state["values"],
                metadata=state.get("metadata"),
            )
            for state in history
        ]
        return api_history
