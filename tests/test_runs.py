# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
from datetime import datetime
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from agent_workflow_server.agents.load import load_agents
from agent_workflow_server.generated.models.run_search_request import (
    RunSearchRequest,
)
from agent_workflow_server.services.queue import start_workers
from agent_workflow_server.services.runs import ApiRun, ApiRunCreate, Runs
from agent_workflow_server.storage.storage import DB
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


def init_test_search_runs(
    agent_id: str, nb_pending: int, nb_success: int, nb_error: int
):
    status = ["pending"] * nb_pending + ["success"] * nb_success + ["error"] * nb_error
    for i in range(nb_pending + nb_success + nb_error):
        run = {
            "run_id": str(uuid4()),
            "agent_id": agent_id,
            "thread_id": str(uuid4()),  # TODO
            "input": {},
            "config": None,
            "metadata": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": status[i],
        }
        DB.create_run(run)


TEST_SEARCH_RUNS_AGENT_ID_2 = "2f1e2549-5799-4321-91ae-2a4881d55526"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "agent_id, status, expected, exception",
    [
        (MOCK_AGENT_ID, "success", 2, False),
        (MOCK_AGENT_ID, "pending", 5, False),
        (MOCK_AGENT_ID, "error", 1, False),
        (MOCK_AGENT_ID, "timeout", 0, False),
        (MOCK_AGENT_ID, "interrupted", 0, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "success", 1, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "pending", 1, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "error", 0, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "timeout", 0, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "interrupted", 0, False),
        ("unk-agent-id", "success", 0, False),
        ("unk-agent-id", "pending", 0, False),
        (None, "success", 3, False),
        (None, "pending", 6, False),
        (None, "error", 1, False),
        (MOCK_AGENT_ID, None, 8, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, None, 2, False),
        ("unk-agent-id", None, 0, False),
        (None, None, 10, False),
    ],
)
async def test_search_runs(
    mocker: MockerFixture,
    agent_id: str | None,
    status: str | None,
    expected: int,
    exception: bool,
):
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    try:
        load_agents()

        # delete all previous runs to avoid count issues for this test
        for run in Runs.get_all():
            Runs.delete(run.run_id)

        # Create test runs DB
        init_test_search_runs(
            MOCK_AGENT_ID,
            nb_pending=5,
            nb_success=2,
            nb_error=1,
        )
        init_test_search_runs(
            TEST_SEARCH_RUNS_AGENT_ID_2,
            nb_pending=1,
            nb_success=1,
            nb_error=0,
        )

        try:
            runs = Runs.search(RunSearchRequest(agent_id=agent_id, status=status))

            assert not exception
            assert len(runs) == expected

        except ValueError:
            assert exception
        except Exception as e:
            print(f"Unexpected exception: {e}")
            assert False

    finally:
        # delete all previous runs to avoid count issues for other tests
        for run in Runs.get_all():
            Runs.delete(run.run_id)
