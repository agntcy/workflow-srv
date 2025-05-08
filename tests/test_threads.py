# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from uuid import uuid4

import pytest
from pytest_mock import MockerFixture

from agent_workflow_server.generated.models.thread_create import ThreadCreate
from agent_workflow_server.services.threads import (
    DuplicatedThreadError,
    Threads,
)
from agent_workflow_server.storage.storage import DB


@pytest.fixture(scope="function", autouse=True)
def clean_db():
    """Create a clean test database instance before each test and clean it after the test completes"""
    # Store original DB state
    original_runs = dict(DB._runs)
    original_runs_info = dict(DB._runs_info)
    original_runs_output = dict(DB._runs_output)
    original_threads = dict(DB._threads)

    # Clear the DB for the test
    DB._runs.clear()
    DB._runs_info.clear()
    DB._runs_output.clear()
    DB._threads.clear()

    # Run the test
    yield

    # Clean up after the test
    DB._runs.clear()
    DB._runs_info.clear()
    DB._runs_output.clear()
    DB._threads.clear()

    # Restore original state if needed (optional)
    # Comment this out if you don't want to preserve existing DB data
    DB._runs.update(original_runs)
    DB._runs_info.update(original_runs_info)
    DB._runs_output.update(original_runs_output)
    DB._threads.update(original_threads)


@pytest.fixture
def mock_thread():
    thread_id = str(uuid4())
    thread = {
        "thread_id": thread_id,
        "metadata": {"key": "value"},
        "status": "idle",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    DB.create_thread(thread)

    thread_id2 = str(uuid4())
    thread2 = {
        "thread_id": thread_id2,
        "metadata": {"key": "value2"},
        "status": "busy",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    DB.create_thread(thread2)

    thread_id3 = str(uuid4())
    thread3 = {
        "thread_id": thread_id3,
        "metadata": {"key": "value3"},
        "status": "idle",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    DB.create_thread(thread3)

    return thread


@pytest.fixture
def mock_agent(mocker: MockerFixture):
    mock_agent = mocker.Mock()
    mock_agent.get_agent_state = mocker.AsyncMock(
        return_value={"values": {"key": "value"}}
    )
    mock_agent.get_history = mocker.AsyncMock(
        return_value=[
            {
                "checkpoint_id": "checkpoint1",
                "values": {"key1": "value1"},
                "metadata": {"meta": "data1"},
            },
            {
                "checkpoint_id": "checkpoint2",
                "values": {"key2": "value2"},
                "metadata": {"meta": "data2"},
            },
        ]
    )

    # Mock AGENTS dictionary
    mock_agents = {"mock_agent": mocker.Mock(agent=mock_agent)}
    mocker.patch("agent_workflow_server.services.threads.AGENTS", mock_agents)

    return mock_agent


@pytest.mark.asyncio
async def test_get_thread_by_id(mock_thread, mock_agent):
    # Test retrieving an existing thread
    thread = await Threads.get_thread_by_id(mock_thread["thread_id"])
    assert thread is not None
    assert thread.thread_id == mock_thread["thread_id"]
    assert thread.metadata == mock_thread["metadata"]
    assert thread.status == mock_thread["status"]
    assert thread.values == {"key": "value"}

    # Test retrieving non-existent thread
    thread = await Threads.get_thread_by_id("nonexistent_id")
    assert thread is None

    # Verify agent's get_agent_state was called
    mock_agent.get_agent_state.assert_called_once_with(mock_thread["thread_id"])


@pytest.mark.asyncio
async def test_create_thread():
    # Test creating a new thread with generated ID
    thread_create = ThreadCreate(metadata={"key": "value"})
    thread = await Threads.create_thread(thread_create, False)
    assert thread is not None
    assert thread.metadata == {"key": "value"}
    assert thread.status == "idle"

    # Test creating a thread with specified ID
    thread_id = str(uuid4())
    thread_create = ThreadCreate(thread_id=thread_id, metadata={"key": "value2"})
    thread = await Threads.create_thread(thread_create, False)
    assert thread is not None
    assert thread.thread_id == thread_id
    assert thread.metadata == {"key": "value2"}

    # Test creating a thread with existing ID (without raising error)
    thread_create = ThreadCreate(thread_id=thread_id, metadata={"key": "value3"})
    thread = await Threads.create_thread(thread_create, False)
    assert thread is not None
    assert thread.thread_id == thread_id
    assert thread.metadata == {"key": "value2"}  # should not be updated

    # Test creating a thread with existing ID (with raising error)
    thread_create = ThreadCreate(thread_id=thread_id, metadata={"key": "value3"})
    with pytest.raises(DuplicatedThreadError):
        await Threads.create_thread(thread_create, True)


@pytest.mark.asyncio
async def test_copy_thread(mock_thread):
    # Test copying an existing thread
    copied_thread = await Threads.copy_thread(mock_thread["thread_id"])
    assert copied_thread is not None
    assert copied_thread.thread_id != mock_thread["thread_id"]
    assert copied_thread.metadata == mock_thread["metadata"]
    assert copied_thread.status == mock_thread["status"]

    # Test copying non-existent thread
    copied_thread = await Threads.copy_thread("nonexistent_id")
    assert copied_thread is None


@pytest.mark.asyncio
async def test_list_threads(mock_thread):
    threads = await Threads.list_threads()
    assert len(threads) >= 1
    assert any(t.thread_id == mock_thread["thread_id"] for t in threads)


@pytest.mark.asyncio
async def test_update_thread(mock_thread, mock_agent):
    # Test updating an existing thread
    updates = {"metadata": {"new_key": "new_value"}}
    updated_thread = await Threads.update_thread(mock_thread["thread_id"], updates)
    assert updated_thread is not None
    assert updated_thread.metadata == {"new_key": "new_value"}

    # Test updating non-existent thread
    updated_thread = await Threads.update_thread("nonexistent_id", updates)
    assert updated_thread is None


@pytest.mark.asyncio
async def test_search(mock_thread):
    threads = await Threads.search(filters={"status": "idle"})
    assert len(threads) >= 1
    assert any(t.thread_id == mock_thread["thread_id"] for t in threads)

    # Test searching for threads
    threads = await Threads.search(filters={"status": "idle"}, limit=2, offset=0)
    assert len(threads) >= 1
    assert len(threads) <= 2
    assert any(t.thread_id == mock_thread["thread_id"] for t in threads)

    # Test searching for threads
    threads = await Threads.search(filters={"status": "idle"}, limit=2, offset=1)
    assert len(threads) == 1

    # Test searching with no matches
    threads = await Threads.search(
        filters={"status": "nonexistent_status"}, limit=10, offset=0
    )
    assert len(threads) == 0


@pytest.mark.asyncio
async def test_get_history(mock_thread, mock_agent):
    # Test getting thread history
    history = await Threads.get_history(mock_thread["thread_id"], 10, 0)
    assert len(history) == 2
    assert history[0].checkpoint.checkpoint_id == "checkpoint1"
    assert history[0].values == {"key1": "value1"}
    assert history[0].metadata == {"meta": "data1"}
    assert history[1].checkpoint.checkpoint_id == "checkpoint2"

    # Verify agent's get_history was called with correct parameters
    mock_agent.get_history.assert_called_once_with(mock_thread["thread_id"], 10, 0)


@pytest.mark.asyncio
async def test_check_pending_runs(mocker: MockerFixture):
    thread_id = str(uuid4())

    # Mock DB search_run to simulate no pending runs
    mocker.patch("agent_workflow_server.storage.storage.DB.search_run", return_value=[])
    has_pending = await Threads.check_pending_runs(thread_id)
    assert not has_pending

    # Mock DB search_run to simulate pending runs
    mocker.patch(
        "agent_workflow_server.storage.storage.DB.search_run",
        return_value=[{"run_id": "123"}],
    )
    has_pending = await Threads.check_pending_runs(thread_id)
    assert has_pending
