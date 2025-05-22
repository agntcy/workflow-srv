# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from datetime import datetime
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from agent_workflow_server.agents.load import load_agents
from agent_workflow_server.generated.models.config import Config
from agent_workflow_server.generated.models.run_search_request import (
    RunSearchRequest,
)
from agent_workflow_server.services.queue import start_workers
from agent_workflow_server.services.runs import ApiRun, ApiRunCreate, Runs
from agent_workflow_server.storage.models import RunStatus
from agent_workflow_server.storage.storage import DB
from tests.mock import (
    MOCK_AGENT_ID,
    MOCK_RUN_INPUT,
    MOCK_RUN_INPUT_ERROR,
    MOCK_RUN_INPUT_INTERRUPT,
    MOCK_RUN_INPUT_STREAM,
    MOCK_RUN_OUTPUT,
    MOCK_RUN_OUTPUT_ERROR,
    MOCK_RUN_OUTPUT_INTERRUPT,
    MOCK_RUN_OUTPUT_STREAM,
    MOCK_WEBSERVER_DEFAULT_HOST,
    MOCK_WEBSERVER_DEFAULT_PORT,
    MOCK_WEBSERVER_WEBHOOK_PATH,
    MockAdapter,
    TestWebServer,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "run_create_mock, expected_status, expected_output",
    [
        (
            ApiRunCreate(
                agent_id=MOCK_AGENT_ID,
                input=MOCK_RUN_INPUT,
                config=Config(
                    tags=["test"],
                    recursion_limit=3,
                    configurable={"mock-key": "mock-value"},
                ),
                webhook=f"http://{MOCK_WEBSERVER_DEFAULT_HOST}:{MOCK_WEBSERVER_DEFAULT_PORT}/{MOCK_WEBSERVER_WEBHOOK_PATH}",
            ),
            "success",
            MOCK_RUN_OUTPUT,
        ),
        (
            ApiRunCreate(
                agent_id=MOCK_AGENT_ID,
                input=MOCK_RUN_INPUT,
            ),
            "success",
            MOCK_RUN_OUTPUT,
        ),
        (
            ApiRunCreate(agent_id=MOCK_AGENT_ID, input=MOCK_RUN_INPUT_INTERRUPT),
            "interrupted",
            MOCK_RUN_OUTPUT_INTERRUPT,
        ),
        (
            ApiRunCreate(agent_id=MOCK_AGENT_ID, input=MOCK_RUN_INPUT_ERROR),
            "error",
            MOCK_RUN_OUTPUT_ERROR,
        ),
    ],
)
async def test_invoke(
    mocker: MockerFixture,
    run_create_mock: ApiRunCreate,
    expected_status: RunStatus,
    expected_output: dict,
):
    if run_create_mock.webhook:
        mock_server = TestWebServer(
            host=MOCK_WEBSERVER_DEFAULT_HOST,
            port=MOCK_WEBSERVER_DEFAULT_PORT,
            path=MOCK_WEBSERVER_WEBHOOK_PATH,
        )
        await mock_server.start()

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

        assert run.status == expected_status
        assert run.run_id == new_run.run_id
        assert run.agent_id == run_create_mock.agent_id
        assert run.creation.agent_id == run_create_mock.agent_id
        assert run.creation.input == run_create_mock.input
        assert run.creation.config == run_create_mock.config
        assert run.creation.webhook == run_create_mock.webhook
        assert output == expected_output

        # Check if the webhook was called with the expected payload
        if run_create_mock.webhook:
            assert mock_server.webhook_payload.decode("utf-8") == run.model_dump_json(
                by_alias=True, exclude_unset=True
            )

    finally:
        worker_task.cancel()
        if run_create_mock.webhook and mock_server:
            await mock_server.stop()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
@pytest.mark.parametrize("timeout", [0.5, 1, 1.0, 2.51293])
async def test_invoke_timeout(mocker: MockerFixture, timeout: float):
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    run_create_mock = ApiRunCreate(agent_id=MOCK_AGENT_ID, input=MOCK_RUN_INPUT)

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
            "webhook": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": status[i],
        }
        DB.create_run(run)


TEST_SEARCH_RUNS_AGENT_ID_1 = MOCK_AGENT_ID
TEST_SEARCH_RUNS_AGENT_ID_2 = "2f1e2549-5799-4321-91ae-2a4881d55526"
TEST_SEARCH_RUNS_AGENT_ID_3 = "26aee4b6-1749-4877-bcd9-a580fa3974b9"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "agent_id, status, expected, offset, limit, exception",
    [
        (TEST_SEARCH_RUNS_AGENT_ID_1, "success", 2, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_1, "pending", 5, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_1, "error", 1, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_1, "timeout", 0, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_1, "interrupted", 0, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "success", 1, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "pending", 1, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "error", 0, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "timeout", 0, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, "interrupted", 0, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_3, "success", 0, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_3, "pending", 0, None, None, False),
        (None, "success", 3, None, None, False),
        (None, "pending", 6, None, None, False),
        (None, "error", 1, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_1, None, 8, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_2, None, 2, None, None, False),
        (TEST_SEARCH_RUNS_AGENT_ID_3, None, 0, None, None, False),
        (None, None, 10, None, None, False),
        (None, None, 4, 0, 4, False),
        (None, None, 4, 4, 4, False),
        (None, None, 2, 8, 4, False),
    ],
)
async def test_search_runs(
    mocker: MockerFixture,
    agent_id: str | None,
    status: str | None,
    expected: int,
    offset: int | None,
    limit: int | None,
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
            TEST_SEARCH_RUNS_AGENT_ID_1,
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
            runs = Runs.search_for_runs(
                RunSearchRequest(
                    agent_id=agent_id, status=status, offset=offset, limit=limit
                )
            )

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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "run_create_mock, expected_status, expected_output",
    [
        (
            ApiRunCreate(
                agent_id=MOCK_AGENT_ID,
                input=MOCK_RUN_INPUT,
                config=Config(
                    tags=["test"],
                    recursion_limit=3,
                    configurable={"mock-key": "mock-value"},
                ),
            ),
            "pending",  # on live-stream "success" comes after the stream is closed.
            MOCK_RUN_OUTPUT,
        ),
        (
            ApiRunCreate(agent_id=MOCK_AGENT_ID, input=MOCK_RUN_INPUT_INTERRUPT),
            "interrupted",
            MOCK_RUN_OUTPUT_INTERRUPT,
        ),
        (
            ApiRunCreate(agent_id=MOCK_AGENT_ID, input=MOCK_RUN_INPUT_ERROR),
            "error",
            MOCK_RUN_OUTPUT_ERROR,
        ),
        (
            ApiRunCreate(agent_id=MOCK_AGENT_ID, input=MOCK_RUN_INPUT_STREAM),
            "pending",
            MOCK_RUN_OUTPUT_STREAM,
        ),
    ],
)
async def test_invoke_stream(
    mocker: MockerFixture,
    run_create_mock: ApiRunCreate,
    expected_status: RunStatus,
    expected_output: dict | list,
):
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    try:
        load_agents()

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(start_workers(1))

        new_run = await Runs.put(run_create=run_create_mock)

        assert isinstance(new_run, ApiRun)
        assert new_run.creation.input == run_create_mock.input
        assert new_run.agent_id == run_create_mock.agent_id
        assert new_run.creation.agent_id == run_create_mock.agent_id
        assert new_run.creation.config == run_create_mock.config

        try:
            async for event in Runs.stream_events(run_id=new_run.run_id):
                if isinstance(expected_output, list):
                    exp_output = expected_output.pop(0)
                else:
                    exp_output = expected_output

                if event is None:
                    break  # Errors can generate None at the moment
                elif event.actual_instance.type == "custom":
                    assert False, (
                        f"unsupported stream event payload type: {event.actual_instance.type}"
                    )
                elif event.actual_instance.type == "values":
                    # Not canonical, but close enough.
                    output = json.dumps(event.actual_instance.values, sort_keys=True)
                    expected_json = json.dumps(exp_output, sort_keys=True)

                    assert event.actual_instance.run_id == new_run.run_id
                    assert output == expected_json
                    assert event.actual_instance.status == expected_status
                elif event.actual_instance.type == "interrupt":
                    output = json.dumps(event.actual_instance.interrupt, sort_keys=True)
                    expected_json = json.dumps(exp_output, sort_keys=True)

                    assert event.actual_instance.run_id == new_run.run_id
                    assert output == expected_json
                    assert event.actual_instance.status == expected_status
                elif event.actual_instance.type == "error":
                    output = event.actual_instance.description

                    assert event.actual_instance.run_id == new_run.run_id
                    assert output == exp_output
                    assert event.actual_instance.status == expected_status
                else:
                    assert False, (
                        f"unknown stream event payload type: {event.actual_instance.type}"
                    )

        except asyncio.TimeoutError:
            assert False
        else:
            assert True
    finally:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
