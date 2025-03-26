# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import logging
import traceback
from datetime import datetime
from typing import Literal

from agent_workflow_server.services.validation import (
    InvalidFormatException,
    validate_output,
)
from agent_workflow_server.storage.models import RunInfo
from agent_workflow_server.storage.storage import DB

from .message import Message
from .runs import RUNS_QUEUE, Runs
from .stream import stream_run

MAX_RETRY_ATTEMPTS = 3

logger = logging.getLogger(__name__)


class RunError(Exception): ...


class AttemptsExceededError(Exception): ...


async def start_workers(n_workers: int):
    logger.info(f"Starting {n_workers} workers")
    tasks = [asyncio.create_task(worker(i + 1)) for i in range(n_workers)]
    try:
        await asyncio.gather(*tasks)
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def log_run(
    worker_id: int,
    run_id: str,
    info: Literal["started", "succeeded", "failed", "exeeded attempts"],
    **kwargs,
):
    log_methods = {
        "started": logger.info,
        "succeeded": logger.info,
        "failed": logger.warning,
        "exeeded attempts": logger.error,
    }
    log_message = f"(Worker {worker_id}) Background Run {run_id} {info}"
    if kwargs:
        log_message += ": %s"
        log_methods.get(info, logger.info)(log_message, kwargs)
    else:
        log_methods.get(info, logger.info)(log_message)


def run_stats(run_info: RunInfo):
    return {key: run_info[key] for key in ["exec_s", "queue_s", "attempts"]}


async def worker(worker_id: int):
    while True:
        run_id = await RUNS_QUEUE.get()
        run = DB.get_run(run_id)
        run_info = DB.get_run_info(run_id)

        started_at = datetime.now().timestamp()

        await Runs.set_status(run["run_id"], "pending")

        run_info["attempts"] += 1
        run_info["started_at"] = started_at
        run_info["exec_s"] = 0
        DB.update_run_info(run_id, run_info)

        try:
            if run_info["attempts"] > MAX_RETRY_ATTEMPTS:
                raise AttemptsExceededError()

            log_run(worker_id, run_id, "started")

            try:
                await Runs.Stream.subscribe(run_id)  # to create a queue
                stream = stream_run(run)
                last_message = None
                async for message in stream:
                    await Runs.Stream.publish(run_id, message)
                    last_message = message
            except Exception as error:
                await Runs.Stream.publish(
                    run_id, Message(topic="error", data=(str(error)))
                )
                raise RunError(error)

            ended_at = datetime.now().timestamp()

            run_info["ended_at"] = ended_at
            run_info["exec_s"] = ended_at - started_at
            run_info["queue_s"] = started_at - run["created_at"].timestamp()

            DB.update_run_info(run_id, run_info)

            try:
                validate_output(run_id, run["agent_id"], last_message.data)

                DB.add_run_output(run_id, last_message.data)
                await Runs.Stream.publish(run_id, Message(topic="control", data="done"))
                await Runs.set_status(run_id, "success")
                log_run(worker_id, run_id, "succeeded", **run_stats(run_info))

            except InvalidFormatException as error:
                await Runs.Stream.publish(
                    run_id, Message(topic="error", data=str(error))
                )
                log_run(worker_id, run_id, "failed")
                raise RunError(str(error))

        except AttemptsExceededError:
            ended_at = datetime.now().timestamp()
            run_info.update(
                {
                    "ended_at": ended_at,
                    "exec_s": ended_at - started_at,
                    "queue_s": (started_at - run["created_at"].timestamp()),
                }
            )

            DB.update_run_info(run_id, run_info)
            await Runs.set_status(run_id, "error")
            log_run(worker_id, run_id, "exeeded attempts")

        except RunError as error:
            ended_at = datetime.now().timestamp()
            run_info.update(
                {
                    "ended_at": ended_at,
                    "exec_s": ended_at - started_at,
                    "queue_s": (started_at - run["created_at"].timestamp()),
                }
            )

            DB.update_run_info(run_id, run_info)
            await Runs.set_status(run_id, "error")
            DB.add_run_output(run_id, str(error))
            log_run(
                worker_id,
                run_id,
                "failed",
                **{"error": error, **run_stats(run_info)},
            )
            traceback.print_exc()

            await RUNS_QUEUE.put(run_id)  # Re-queue for retry

        finally:
            RUNS_QUEUE.task_done()
