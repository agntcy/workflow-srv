# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictInt, StrictStr
from typing import Any, List, Optional
from typing_extensions import Annotated
from agent_workflow_server.generated.models.thread import Thread
from agent_workflow_server.generated.models.thread_create import ThreadCreate
from agent_workflow_server.generated.models.thread_patch import ThreadPatch
from agent_workflow_server.generated.models.thread_search_request import ThreadSearchRequest
from agent_workflow_server.generated.models.thread_state import ThreadState


class BaseThreadsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseThreadsApi.subclasses = BaseThreadsApi.subclasses + (cls,)
    async def copy_thread(
        self,
        thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")],
    ) -> Thread:
        """Create a new thread with a copy of the state and checkpoints from an existing thread."""
        ...


    async def create_thread(
        self,
        thread_create: ThreadCreate,
    ) -> Thread:
        """Create a new thread. """
        ...


    async def delete_thread(
        self,
        thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")],
    ) -> None:
        """Delete a thread."""
        ...


    async def get_thread(
        self,
        thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")],
    ) -> Thread:
        """Get a thread from its ID. """
        ...


    async def get_thread_history(
        self,
        thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")],
        limit: Optional[StrictInt],
        before: Optional[StrictStr],
    ) -> List[ThreadState]:
        """Get all past states for a thread."""
        ...


    async def patch_thread(
        self,
        thread_id: Annotated[StrictStr, Field(description="The ID of the thread.")],
        thread_patch: ThreadPatch,
    ) -> Thread:
        """Update a thread."""
        ...


    async def search_threads(
        self,
        thread_search_request: ThreadSearchRequest,
    ) -> List[Thread]:
        """Search for threads.  This endpoint also functions as the endpoint to list all threads."""
        ...
