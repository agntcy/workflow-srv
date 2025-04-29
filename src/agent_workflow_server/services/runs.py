# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from itertools import islice
from typing import Any, AsyncGenerator, AsyncIterator, Dict, List, Optional
from uuid import uuid4

from agent_workflow_server.generated.models.run_create_stateless import (
    RunCreateStateless as ApiRunCreate,
)
from agent_workflow_server.generated.models.run_search_request import (
    RunSearchRequest,
)
from agent_workflow_server.generated.models.run_stateless import (
    RunStateless as ApiRun,
)
from agent_workflow_server.generated.models.stream_event_payload import (
    StreamEventPayload,
)
from agent_workflow_server.generated.models.value_run_result_update import (
    ValueRunResultUpdate,
)
from agent_workflow_server.services.threads import Threads
from agent_workflow_server.storage.models import Run, RunInfo, RunStatus
from agent_workflow_server.storage.storage import DB

from ..utils.tools import is_valid_uuid
from .message import Message

logger = logging.getLogger(__name__)

condition = asyncio.Condition()


def _make_run(run_create: ApiRunCreate) -> Run:
    """
    Convert a RunCreate API model to a Run DB model.

    Args:
        run_create (RunCreate): The API model for creating a run.

    Returns:
        Run: The service model representation of the run.
    """

    curr_time = datetime.now()

    if not is_valid_uuid(run_create.agent_id):
        raise ValueError(f'agent_id "{run_create.agent_id}" is not a valid UUID')

    return {
        "run_id": str(uuid4()),
        "agent_id": run_create.agent_id,
        "thread_id": str(uuid4()),  # TODO
        "input": run_create.input,
        "config": run_create.config.model_dump() if run_create.config else None,
        "metadata": run_create.metadata,
        "created_at": curr_time,
        "updated_at": curr_time,
        "status": "pending",
    }


def _to_api_model(run: Run) -> ApiRun:
    """
    Convert a Run service model to a Run API model.

    Args:
        run (Run): The service model representation of a run.

    Returns:
        Run: The API model representation of the run.
    """
    return ApiRun(
        creation=ApiRunCreate(
            agent_id=run["agent_id"],
            thread_id=run["thread_id"],
            input=run["input"],
            metadata=run["metadata"],
            config=run["config"],
            webhook=None,  # TODO
        ),
        run_id=run["run_id"],
        agent_id=run["agent_id"],
        thread_id=run["thread_id"],
        created_at=run["created_at"],
        updated_at=run["updated_at"],
        status=run["status"],
    )


class StreamManager:
    def __init__(self):
        self.queues: Dict[str, List[asyncio.Queue]] = {}

    def get_queues(self, run_id: str) -> List[asyncio.Queue]:
        return self.queues.get(run_id, [])

    async def add_queue(self, run_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.queues.setdefault(run_id, []).append(queue)
        return queue

    async def remove_queue(self, run_id: str, queue: asyncio.Queue):
        self.queues[run_id].remove(queue)

    async def put_message(self, run_id: str, message: Message) -> None:
        queues = self.get_queues(run_id)
        num = len(queues)
        if not queues:
            logger.warning(f"No queues found for run_id {run_id}")
        await asyncio.gather(*(queue.put(message) for queue in queues))
        logger.debug(f"Message put on {num} queues for run_id {run_id}")


stream_manager = StreamManager()
cvs_pending_run = defaultdict(asyncio.Condition)
RUNS_QUEUE = asyncio.Queue()


class Runs:
    @staticmethod
    async def put(run_create: ApiRunCreate) -> ApiRun:
        new_run = _make_run(run_create)
        run_info = RunInfo(
            run_id=new_run["run_id"],
            queued_at=datetime.now(),
            attempts=0,
        )
        DB.create_run(new_run)
        DB.create_run_info(run_info)

        await RUNS_QUEUE.put(new_run["run_id"])
        return _to_api_model(new_run)

    @staticmethod
    def get(run_id: str) -> Optional[ApiRun]:
        run = DB.get_run(run_id)
        if run is None:
            return None

        return _to_api_model(run)

    @staticmethod
    def delete(run_id: str):
        if not DB.delete_run(run_id):
            raise Exception("Run not found")

    @staticmethod
    def get_all() -> List[ApiRun]:
        db_runs = DB.list_runs()
        return [_to_api_model(run) for run in db_runs]

    @staticmethod
    def search_for_runs(search_request: RunSearchRequest) -> List[ApiRun]:
        filters = {}
        if search_request.agent_id:
            filters["agent_id"] = search_request.agent_id
        if search_request.status:
            filters["status"] = search_request.status
        runs = DB.search_run(filters)

        if search_request.metadata and len(search_request.metadata) > 0:
            for run in enumerate(runs):
                thread = Threads.get_thread_by_id(run["thread_id"])
                if thread:
                    for key, value in search_request.metadata.items():
                        if (
                            thread["metadata"].get(key) is not None
                            and thread["metadata"].get(key) != value
                        ):
                            runs.pop(run)

        return list(
            islice(islice(runs, search_request.offset, None), search_request.limit)
        )

    @staticmethod
    async def resume(run_id: str, user_input: Dict[str, Any]) -> ApiRun:
        run = DB.get_run(run_id)
        if run is None:
            raise ValueError("Run not found")
        if run["status"] != "interrupted":
            raise ValueError("Run is not in interrupted state")
        if run.get("interrupt") is None:
            raise ValueError(f"No interrupt found for run {run_id}")

        interrupt = run["interrupt"]
        interrupt["user_data"] = user_input

        DB.update_run(run_id, {"interrupt": interrupt})
        DB.update_run_info(run_id, {"attempts": 0, "queued_at": datetime.now()})
        updated = DB.update_run_status(run_id, "pending")

        await RUNS_QUEUE.put(updated["run_id"])
        return _to_api_model(updated)

    @staticmethod
    async def set_status(run_id: str, status: RunStatus):
        run = DB.get_run(run_id)
        if not run:
            raise Exception("Run not found")

        DB.update_run_status(run_id, status)

        if status != "pending":
            async with cvs_pending_run[run_id]:
                cvs_pending_run[run_id].notify_all()

    @staticmethod
    async def wait(run_id: str):
        run_stream = Runs.Stream.join(run_id)
        last_chunk = None

        try:
            async for event_data in run_stream:
                output = event_data.data
                last_chunk = output
        except Exception as error:
            raise error

        return last_chunk

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
    async def stream_events(run_id: str) -> AsyncIterator[StreamEventPayload | None]:
        async for message in Runs.Stream.join(run_id):
            msg_data = message.data

            if message.type == "control":
                if message.data == "done":
                    break
                elif message.data == "timeout":
                    yield None
                    continue
                else:
                    logger.error(
                        f'received unknown control message "{message.data}" in stream events for run: {run_id}'
                    )
                    continue

            # We need to get the latest value to return
            run = DB.get_run(run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")

            yield StreamEventPayload(
                ValueRunResultUpdate(
                    type="values",
                    run_id=run["run_id"],
                    status=run["status"],
                    values=msg_data,
                )
            )

    class Stream:
        @staticmethod
        async def publish(run_id: str, message: Message) -> None:
            await stream_manager.put_message(run_id, message)

        @staticmethod
        async def subscribe(run_id: str) -> asyncio.Queue:
            queue = await stream_manager.add_queue(run_id)
            logger.debug(f"Subscribed to queue for run_id {run_id}")
            return queue

        @staticmethod
        async def join(
            run_id: str,
        ) -> AsyncGenerator[Message, None]:
            queue = await Runs.Stream.subscribe(run_id)

            # Check after subscribe whether the run is completed to
            # avoid race condition.
            run = DB.get_run(run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")
            if run["status"] != "pending" and queue.empty():
                return

            while True:
                try:
                    message: Message = await asyncio.wait_for(queue.get(), timeout=10)
                    yield message
                    if message.type == "control" and message.data == "done":
                        break
                except TimeoutError as error:
                    logger.error(f"Timeout waiting for run {run_id}: {error}")
                    yield Message(type="control", data="timeout")
