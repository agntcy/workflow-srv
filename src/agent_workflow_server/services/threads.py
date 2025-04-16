import logging
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

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


def _to_api_model(thread: Thread) -> ApiThread:
    """
    Convert a Thread service model to a Thread API model.

    Args:
        thread (Thread): The service model representation of a thread.

    Returns:
        Thread: The API model representation of the thread.
    """
    return ApiThread(
        thread_id=thread["thread_id"],
        metadata=thread["metadata"],
        status=thread["status"],
        created_at=thread["created_at"],
        updated_at=thread["updated_at"],
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

        thread = DB.get_thread(thread_id)
        if thread_id not in DB._threads:
            return None

        return _to_api_model(thread)

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
            states=thread["states"],
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
        """Update a thread"""

        # Check if the thread exists
        thread = DB.get_thread(thread_id)
        if thread is None:
            return None

        # A ThreadPatch object (which is in the updates as a dict) can contain a
        # checkpoint, metadata (for the thread not for the state), values and messages.

        if "metadata" in updates and updates["metadata"]:
            metaUpdates = {"metadata": updates["metadata"]}
            thread = DB.update_thread(thread_id, metaUpdates)

        threadStates = thread["states"]

        # if checkpoint is in updates and has a checkpoint_id in it
        if "checkpoint" in updates and updates["checkpoint"]:
            checkpoint = updates["checkpoint"]
            checkpoint_id = checkpoint["checkpoint_id"]
            # Check if the checkpoint ID already exists in the thread states
            if threadStates is None:
                threadStates = []
            existing_checkpoints = [state["checkpoint_id"] for state in threadStates]
            if checkpoint_id in existing_checkpoints:
                # Update the existing checkpoint state
                for state in threadStates:
                    if state["checkpoint_id"] == checkpoint_id:
                        # update state with new values, messages and metadata
                        state["values"] = updates["values"]
                        state["messages"] = updates["messages"]

            else:
                # Add a new checkpoint state
                threadStates.append(
                    {
                        "checkpoint_id": checkpoint_id,
                        "values": updates["values"],
                        "messages": updates["messages"],
                    }
                )

        # Update the thread with the new states
        stateUpdates = {"states": threadStates}
        thread = DB.update_thread(thread_id, stateUpdates)

        return _to_api_model(thread)

    @staticmethod
    async def delete_thread(thread_id: str) -> bool:
        """Delete a thread"""
        # Get runs associated with the thread and check if any of them pending
        has_pending_runs = await Threads.check_pending_runs(thread_id)
        if has_pending_runs:
            raise PendingRunError(
                f"Thread with ID {thread_id} has pending runs and cannot be deleted."
            )

        return DB.delete_thread(thread_id)

    @staticmethod
    async def search(filters: dict) -> list[ApiThread]:
        """Search for threads based on filters"""
        threads = DB.search_thread(filters)
        return [_to_api_model(thread) for thread in threads]

    @staticmethod
    async def get_thread_state(
        thread_id: str, limit: int, before: str
    ) -> Optional[List[ApiThreadState]]:
        """Get the state of a thread"""
        thread = DB.get_thread(thread_id)
        if thread is None:
            return None

        thread_states = thread["states"]
        if thread_states is None:
            return None

        ## TODO proper handling of limit and before
        ## TODO proper handling of messages and metadata
        return [
            ApiThreadState(
                checkpoint=ApiThreadCheckpoint(checkpoint_id=state["checkpoint_id"]),
                values=state["values"],
                messages=state.get("messages"),
                metadata=state.get("metadata"),
            )
            for state in thread_states
        ]
