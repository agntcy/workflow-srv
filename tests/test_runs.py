import asyncio

import pytest
from pytest_mock import MockerFixture

from agent_workflow_server.agents.load import load_agents
from agent_workflow_server.services.queue import start_workers
from agent_workflow_server.services.runs import ApiRunCreate, Runs
from tests.mock import (
    MOCK_AGENTS_REF_ENV,
    MOCK_MANIFEST_ENV,
    MOCK_RUN_INPUT,
    MOCK_RUN_OUTPUT,
    MockAdapter,
)

run_create_mock = ApiRunCreate(agent_id="mock_agent", input=MOCK_RUN_INPUT, config={})


@pytest.mark.asyncio
async def test_invoke(mocker: MockerFixture):
    mocker.patch.dict("os.environ", {"AGWS_STORAGE_PERSIST": "False"})
    mocker.patch.dict("os.environ", MOCK_AGENTS_REF_ENV)
    mocker.patch.dict("os.environ", MOCK_MANIFEST_ENV)
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    try:
        load_agents()

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(start_workers(1))

        new_run = await Runs.put(run_create=run_create_mock)
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
    mocker.patch.dict("os.environ", {"AGWS_STORAGE_PERSIST": "False"})
    mocker.patch.dict("os.environ", MOCK_AGENTS_REF_ENV)
    mocker.patch.dict("os.environ", MOCK_MANIFEST_ENV)
    mocker.patch("agent_workflow_server.agents.load.ADAPTERS", [MockAdapter()])

    try:
        load_agents()

        loop = asyncio.get_event_loop()
        worker_task = loop.create_task(start_workers(1))

        new_run = await Runs.put(run_create=run_create_mock)
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
    mocker.patch.dict("os.environ", {"AGWS_STORAGE_PERSIST": "False"})

    try:
        run, output = await Runs.wait_for_output(
            run_id="non-existent-run-id", timeout=timeout
        )
        assert run is None
        assert output is None
    except Exception:
        assert False
