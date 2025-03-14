import asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from typing import Any, Dict, List, Optional, AsyncGenerator, NamedTuple
from collections import defaultdict

import logging

from agent_workflow_server.generated.models.run import RunCreate as ApiRunCreate, Run as ApiRun

from agent_workflow_server.storage.models import Run, RunInfo, RunStatus
from agent_workflow_server.storage.storage import DB

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

    return {
        "run_id": str(uuid4()),
        "agent_id": str(uuid4()),  # TODO
        "thread_id": str(uuid4()),  # TODO
        "input": run_create.input if run_create.input else {},
        "config": run_create.config if run_create.config else {},
        "metadata": run_create.metadata if run_create.metadata else {},
        "created_at": curr_time,
        "updated_at": curr_time,
        "status": "pending"
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
            agent_id=run['agent_id'],
            thread_id=run['thread_id'],
            input=run['input'],
            metadata=run['metadata'],
            config=run['config'],
            webhook=None  # TODO
        ),
        run_id=run['run_id'],
        agent_id=run['agent_id'],
        thread_id=run['thread_id'],
        created_at=run['created_at'],
        updated_at=run['updated_at'],
        status=run["status"]
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
            run_id=new_run['run_id'],
            attempts=0,
        )
        DB.create_run(new_run)
        DB.create_run_info(run_info)

        await RUNS_QUEUE.put(new_run['run_id'])
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

        if run['status'] != "pending":
            # If the run is already completed, return the stored output immediately
            return run, DB.get_run_output(run_id)

        # TODO: handle removing cvs when run is completed and there are no more subscribers
        try:
            async with cvs_pending_run[run_id]:
                await asyncio.wait_for(
                    cvs_pending_run[run_id].wait_for(
                        lambda: DB.get_run_status(run_id) != "pending"),
                    timeout=timeout
                )
                status = DB.get_run_status(run_id)
                run = DB.get_run(run_id)
                if status == "success":
                    return run, DB.get_run_output(run_id)
                else:
                    return run, None
        except asyncio.TimeoutError:
            logger.warning(f"Timeout reached while waiting for run {run_id}")
            raise TimeoutError

        return None, None

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
            while True:
                try:
                    message: Message = await asyncio.wait_for(queue.get(), timeout=1)
                    if message.topic == "control" and message.data == "done":
                        break
                    yield message
                except TimeoutError as error:
                    logger.error(f"Timeout waiting for run {run_id}: {error}")
