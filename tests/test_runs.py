# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio

import pytest
from pytest_mock import MockerFixture

from agent_workflow_server.agents.load import load_agents
from agent_workflow_server.generated.models.run_search_request import (
    RunSearchRequest,
)
from agent_workflow_server.services.queue import start_workers
from agent_workflow_server.services.runs import ApiRun, ApiRunCreate, Runs
from tests.mock import (
    MOCK_AGENT_ID,
    MOCK_RUN_INPUT,
    MOCK_RUN_OUTPUT,
    MockAdapter,
)

run_create_mock = ApiRunCreate(agent_id=MOCK_AGENT_ID, input=MOCK_RUN_INPUT, config={})


@pytest.mark.asyncio
async def test_invoke(mocker: MockerFixture):
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    try:
        load_agents()

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(start_workers(1))

        new_run = await Runs.put(run_create=run_create_mock)
        assert isinstance(new_run, ApiRun)
        assert new_run.creation.input == run_create_mock.input

        try:
            run, output = await Runs.wait_for_output(run_id=new_run.run_id)
        except asyncio.TimeoutError:
            assert False
        else:
            assert True

        assert run.status == "success"
        assert run.run_id == new_run.run_id
        assert output == MOCK_RUN_OUTPUT
    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
@pytest.mark.parametrize("timeout", [0.5, 1, 1.0, 2.51293])
async def test_invoke_timeout(mocker: MockerFixture, timeout: float):
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    try:
        load_agents()

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(start_workers(1))

        new_run = await Runs.put(run_create=run_create_mock)
        assert isinstance(new_run, ApiRun)
        assert new_run.creation.input == run_create_mock.input

        try:
            run, output = await Runs.wait_for_output(
                run_id=new_run.run_id, timeout=timeout
            )
        except asyncio.TimeoutError:
            assert True
        else:
            assert False
    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
@pytest.mark.parametrize("timeout", [0.5, 1, 5, None])
async def test_wait_invalid_run(mocker: MockerFixture, timeout: float | None):
    try:
        run, output = await Runs.wait_for_output(
            run_id="non-existent-run-id", timeout=timeout
        )
        assert run is None
        assert output is None
    except Exception:
        assert False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "valid_agent_id, status, expected, exception",
    [
        (True, "success", 0, False),
        (True, "pending", 1, False),
        (True, "error", 0, False),
        (True, "timeout", 0, False),
        (True, "interrupted", 0, False),
        (False, "success", 0, False),
        (False, "pending", 0, False),
        (None, "success", 0, False),
        (None, "pending", 1, False),
        (None, "error", 0, False),
        (True, None, 1, False),
        (False, None, 0, False),
        (None, None, 0, True),
    ],
)
async def test_search_runs(
    mocker: MockerFixture,
    valid_agent_id: bool | None,
    status: str | None,
    expected: int,
    exception: bool,
):
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    try:
        load_agents()

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(start_workers(1))

        # delete all previous runs to avoid count issues
        runs = Runs.get_all()
        for run in runs:
            Runs.delete(run.run_id)

        # Create the run
        new_run = await Runs.put(run_create=run_create_mock)

        try:
            agent_id = None
            if valid_agent_id is not None:
                agent_id = (
                    new_run.agent_id if valid_agent_id else "non-existent-agent-id"
                )

            runs = Runs.search(RunSearchRequest(agent_id=agent_id, status=status))

            assert not exception
            assert len(runs) == expected

        except ValueError:
            assert exception
        except Exception as e:
            print(f"Unexpected exception: {e}")
            assert False

    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
