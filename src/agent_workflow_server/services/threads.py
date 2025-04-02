import logging
from datetime import datetime
from typing import Optional
from uuid import uuid4

from agent_workflow_server.generated.models.thread import (
    Thread as ApiThread,
)
from agent_workflow_server.generated.models.thread_create import ThreadCreate
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


class Threads:
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
        thread = DB.update_thread(thread_id, updates)
        if thread is None:
            return None
        return _to_api_model(thread)

    @staticmethod
    async def delete_thread(thread_id: str) -> bool:
        """Delete a thread"""
        # TODO If the thread contains any pending run, deletion fails.
        return DB.delete_thread(thread_id)

    @staticmethod
    async def search(filters: dict) -> list[ApiThread]:
        """Search for threads based on filters"""
        threads = DB.search_thread(filters)
        return [_to_api_model(thread) for thread in threads]
