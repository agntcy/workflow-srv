# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
from datetime import datetime
from typing import Literal

from agent_workflow_server.services.validation import (
    InvalidFormatException,
    validate_output,
)
from agent_workflow_server.storage.models import Interrupt, RunInfo
from agent_workflow_server.storage.storage import DB
from agent_workflow_server.utils.tools import make_serializable

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
    info: Literal[
        "got message",
        "started",
        "interrupted",
        "succeeded",
        "failed",
        "exeeded attempts",
    ],
    **kwargs,
):
    log_methods = {
        "got message": logger.debug,
        "started": logger.info,
        "interrupted": logger.info,
        "succeeded": logger.info,
        "failed": logger.exception,
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
                    message.data = make_serializable(message.data)
                    await Runs.Stream.publish(run_id, message)
                    last_message = message
                    if last_message.type == "interrupt":
                        log_run(
                            worker_id,
                            run_id,
                            "interrupted",
                            message_data=json.dumps(message.data),
                        )
                        break
            except Exception as error:
                await Runs.Stream.publish(
                    run_id, Message(type="message", data=(str(error)))
                )
                raise RunError(error)

            ended_at = datetime.now().timestamp()

            run_info["ended_at"] = ended_at
            run_info["exec_s"] = ended_at - started_at
            run_info["queue_s"] = started_at - run_info["queued_at"].timestamp()

            DB.update_run_info(run_id, run_info)

            try:
                validate_output(run_id, run["agent_id"], last_message.data)
                log_run(
                    worker_id,
                    run_id,
                    "got message",
                    message_data=json.dumps(last_message.data),
                )
                DB.add_run_output(run_id, last_message.data)
                await Runs.Stream.publish(run_id, Message(type="control", data="done"))
                if last_message.type == "interrupt":
                    interrupt = Interrupt(
                        event=last_message.event, ai_data=last_message.data
                    )
                    DB.update_run(run_id, {"interrupt": interrupt})
                    await Runs.set_status(run_id, "interrupted")
                else:
                    await Runs.set_status(run_id, "success")
                log_run(worker_id, run_id, "succeeded", **run_stats(run_info))

            except InvalidFormatException as error:
                await Runs.Stream.publish(
                    run_id, Message(type="message", data=str(error))
                )
                log_run(worker_id, run_id, "failed")
                raise RunError(str(error))

        except AttemptsExceededError:
            ended_at = datetime.now().timestamp()
            run_info.update(
                {
                    "ended_at": ended_at,
                    "exec_s": ended_at - started_at,
                    "queue_s": (started_at - run_info["queued_at"].timestamp()),
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
                    "queue_s": (started_at - run_info["queued_at"].timestamp()),
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

            await RUNS_QUEUE.put(run_id)  # Re-queue for retry

        finally:
            RUNS_QUEUE.task_done()
