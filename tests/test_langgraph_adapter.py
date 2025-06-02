# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from uuid import uuid4

import pytest

from agent_workflow_server.agents.adapters.langgraph import (
    LangGraphAdapter,
    LangGraphAgent,
)
from agent_workflow_server.storage.models import Interrupt, Run
from agent_workflow_server.storage.storage import DB
from tests.agents.mailcomposer import CreateLanggraphWorkflow, GetLanggraphWorkflow
from tests.tools import _read_manifest

logger = logging.getLogger(__name__)

MOCK_AGENT_ID = "3f1e2549-5799-4321-91ae-2a4881d55526"
MOCK_RUN_INPUT = {
    "messages": [{"type": "human", "content": "ceci est un mail"}],
    "is_completed": False,
}


@pytest.mark.asyncio
async def test_langgraph_astream():
    expected = ["ceci est un mail", "this is a placeholder for the AI response"]

    w = CreateLanggraphWorkflow()

    manifest_path = "tests/agents/mailcomposer.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LangGraphAdapter()  # Replace with actual adapter initialization
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LangGraphAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config={"tags": ["test", "langgraph"]},
    )

    events = []
    async for result in agent.astream(new_run):
        messages = result.data.get("messages", [])
        for message in messages:
            events.append(message.content)

    assert len(events) == len(expected), (
        "Unexpected number of events generated during the run"
    )
    for i, event in enumerate(events):
        assert event == expected[i], (
            f"Event {i} does not match expected value: {event} != {expected[i]}"
        )


@pytest.mark.asyncio
async def test_langgraph_get_agent_state():
    expected = [
        "ceci est un mail",
        "ceci est un mail",
        "this is a placeholder for the AI response",
    ]

    w = GetLanggraphWorkflow()

    manifest_path = "tests/agents/mailcomposer.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LangGraphAdapter()  # Replace with actual adapter initialization
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LangGraphAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config={"tags": ["test", "langgraph"]},
    )

    async for _ in agent.astream(new_run):
        pass

    state = await agent.get_agent_state(thread_id)
    assert state is not None, "Agent state should not be None"
    assert isinstance(state, dict), "Agent state should be a dictionary"
    assert "checkpoint_id" in state, "Checkpoint ID should be present in the state"
    assert "values" in state, "State values should be present in the state"
    assert "messages" in state["values"], "Messages should be present in state values"
    assert isinstance(state["values"]["messages"], list), (
        "Messages should be a list in state values"
    )

    messages = state["values"]["messages"]
    events = []
    for message in messages:
        events.append(message.content)

    assert len(events) == len(expected), (
        "Unexpected number of events generated during the run"
    )
    for i, event in enumerate(events):
        assert event == expected[i], (
            f"Event {i} does not match expected value: {event} != {expected[i]}"
        )


@pytest.mark.asyncio
async def test_langgraph_get_history():
    expected = {
        1: {"source": "loop", "writes": "email_agent", "step": 1},
        0: {"source": "loop", "writes": None, "step": 0},
        -1: {"source": "input", "writes": "__start__", "step": -1},
    }

    w = GetLanggraphWorkflow()

    manifest_path = "tests/agents/mailcomposer.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LangGraphAdapter()  # Replace with actual adapter initialization
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LangGraphAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config={"tags": ["test", "langgraph"]},
    )

    async for _ in agent.astream(new_run):
        pass

    history = await agent.get_history(thread_id, None, None)
    assert history is not None, "History should not be None"
    assert isinstance(history, list), "History should be a list"

    checkpoints = []
    for item in history:
        assert isinstance(item, dict), "History item should be a dictionary"
        assert "checkpoint_id" in item, "Checkpoint ID should be present"
        assert "metadata" in item, "Metadata should be present in history item"
        assert "source" in item["metadata"], "Source should be present in metadata"
        assert "writes" in item["metadata"], "Writes should be present in metadata"
        assert "step" in item["metadata"], "Step should be present in metadata"
        checkpoints.append(item)

    assert len(checkpoints) == len(expected), (
        "Unexpected number of events generated during the run"
    )
    for i, item in enumerate(checkpoints):
        expected_item = expected[item["metadata"]["step"]]
        assert item["metadata"]["source"] == expected_item["source"], (
            f"Item {i} source does not match expected value: {item['metadata']['source']} != {expected_item['source']}"
        )
        if expected_item["writes"] is None:
            assert item["metadata"]["writes"] is None, (
                f"Item {i} writes should be None but got {item['metadata']['writes']}"
            )
        else:
            assert expected_item["writes"] in item["metadata"]["writes"], (
                f"Item {i} writes does not match expected value: {item['metadata']['writes']} != {expected_item['writes']}"
            )


@pytest.mark.asyncio
async def test_langgraph_update_agent_state():
    w = GetLanggraphWorkflow()

    manifest_path = "tests/agents/mailcomposer.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LangGraphAdapter()  # Replace with actual adapter initialization
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LangGraphAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config={"tags": ["test", "langgraph"]},
    )

    async for _ in agent.astream(new_run):
        pass

    history = await agent.get_history(thread_id, None, None)
    assert history is not None, "History should not be None"
    assert isinstance(history, list), "History should be a list"
    history_length = len(history)

    checkpoint_id = str(uuid4())
    new_checkpoint = {
        "checkpoint_id": checkpoint_id,
        "values": {
            "accepted_events": [],
            "broker_log": [],
            "event_buffers": {},
            "globals": {},
            "is_running": False,
            "stepwise": False,
            "streaming_queue": "[]",
        },
    }
    _ = await agent.update_agent_state(thread_id, new_checkpoint)

    history = await agent.get_history(thread_id, None, None)
    assert history is not None, "History should not be None"
    assert isinstance(history, list), "History should be a list"
    assert len(history) == history_length + 1, (
        "History length should have increased by 1 after updating agent state"
    )


@pytest.mark.asyncio
async def test_langgraph_astream_with_interrupt():
    w = GetLanggraphWorkflow()

    manifest_path = "tests/agents/mailcomposer.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LangGraphAdapter()  # Replace with actual adapter initialization
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LangGraphAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config={"tags": ["test", "langgraph"]},
        interrupt=Interrupt(
            event="interrupt_event",
            name="format_email",
            ai_data={"key": "value"},
        ),
    )

    print("First run with interrupt")
    events = []
    async for result in agent.astream(new_run):
        events.append(result.data)
    print(len(events), "events received")
    print("Events after first run with interrupt:", events[0])
    assert len(events) == 1, "Expected only one event due to interrupt"
    assert "messages" in events[0], "Expected 'messages' key in the event data"
    assert isinstance(events[0]["messages"], list), "Expected 'messages' to be a list"
    assert len(events[0]["messages"]) == 2, "Expected two keys in the event data"

    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config=None,
        interrupt=Interrupt(
            event="interrupt_event",
            name="format_email",
            ai_data={"key": "value"},
            user_data={"type": "human", "content": "ceci est un mail"},
        ),
    )

    print("Second run")
    events = []
    async for result in agent.astream(new_run):
        events.append(result.data)
    print(len(events), "events received")
    print("Events after second run:", events)
