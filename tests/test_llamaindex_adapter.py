# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from uuid import uuid4

import pytest

from agent_workflow_server.agents.adapters.llamaindex import (
    LlamaIndexAdapter,
    LlamaIndexAgent,
)
from agent_workflow_server.storage.models import Interrupt, Run
from agent_workflow_server.storage.storage import DB
from tests.agents.jokeflow import JokeFlow
from tests.agents.jokereviewer import JokeReviewer
from tests.tools import _read_manifest

logger = logging.getLogger(__name__)


MOCK_AGENT_ID = "3f1e2549-5799-4321-91ae-2a4881d55526"
MOCK_RUN_INPUT = {"topic": "pirates"}
MOCK_RUN_OUTPUT = {
    "result": "this is a critique of the joke: this is a joke about pirates"
}
EVENTS_CONTENT_KEYS = [
    "accepted_events",
    "broker_log",
    "event_buffers",
    "globals",
    "in_progress",
    "is_running",
    "queues",
    "stepwise",
    "streaming_queue",
]


@pytest.mark.asyncio
async def test_llamaindex_astream():
    expected = [{}, "this is a critique of the joke: this is a joke about pirates"]

    w = JokeFlow(timeout=60, verbose=False)
    manifest_path = "tests/agents/jokeflow_manifest.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LlamaIndexAdapter()
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest.extensions[0].data.deployment,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LlamaIndexAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config=None,
    )

    events = []
    async for result in agent.astream(new_run):
        events.append(result.data)

    assert len(events) == len(expected), (
        "Unexpected number of events generated during the run"
    )
    for i, event in enumerate(events):
        assert event == expected[i], (
            f"Event {i} does not match expected value: {event} != {expected[i]}"
        )


@pytest.mark.asyncio
async def test_llamaindex_get_agent_state():
    w = JokeFlow(timeout=60, verbose=False)
    manifest_path = "tests/agents/jokeflow_manifest.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LlamaIndexAdapter()
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest.extensions[0].data.deployment,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LlamaIndexAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config=None,
    )

    checkpoints = []
    async for _ in agent.astream(new_run):
        state = await agent.get_agent_state(thread_id)
        assert state is not None, "Agent state should not be None"
        assert isinstance(state, dict), "Agent state should be a dictionary"
        assert "checkpoint_id" in state, "Checkpoint ID should be present in the state"
        assert (key in state["values"].keys() for key in EVENTS_CONTENT_KEYS), (
            "State values should contain expected keys"
        )
        assert state["checkpoint_id"] not in checkpoints, (
            "Checkpoint ID should be unique"
        )
        checkpoints.append(state)


@pytest.mark.asyncio
async def test_llamaindex_get_history():
    w = JokeFlow(timeout=60, verbose=False)
    manifest_path = "tests/agents/jokeflow_manifest.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LlamaIndexAdapter()
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest.extensions[0].data.deployment,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LlamaIndexAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config=None,
    )

    events = []
    async for result in agent.astream(new_run):
        events.append(result.data)

        history = await agent.get_history(thread_id, None, None)
        assert history is not None, "History should not be None"
        assert isinstance(history, list), "History should be a list"
        assert len(events) == len(history)

        checkpoints = []
        for item in history:
            print(json.dumps(item, indent=4, sort_keys=True))
            assert isinstance(item, dict), "History item should be a dictionary"
            assert "checkpoint_id" in item, "Checkpoint ID should be present"
            assert (key in item["values"].keys() for key in EVENTS_CONTENT_KEYS), (
                "Hist values should contain expected keys"
            )
            assert item["checkpoint_id"] not in checkpoints, (
                "Checkpoint ID should be unique"
            )
            checkpoints.append(item)


@pytest.mark.asyncio
async def test_llamaindex_update_agent_state():
    expected = [{}, "this is a critique of the joke: this is a joke about pirates"]

    w = JokeFlow(timeout=60, verbose=False)
    manifest_path = "tests/agents/jokeflow_manifest.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LlamaIndexAdapter()  # Replace with actual adapter initialization
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest.extensions[0].data.deployment,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LlamaIndexAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config=None,
    )

    events = []
    async for result in agent.astream(new_run):
        events.append(result.data)
    assert len(events) == len(expected), (
        "Unexpected number of events generated during the run"
    )
    for i, event in enumerate(events):
        assert event == expected[i], (
            f"Event {i} does not match expected value: {event} != {expected[i]}"
        )

    history = await agent.get_history(thread_id, None, None)
    assert history is not None
    assert isinstance(history, list)
    assert len(history) == 2

    checkpoint_id = str(uuid4())
    new_checkpoint = {
        "checkpoint_id": checkpoint_id,
        "values": {
            "accepted_events": [
                ["generate_joke", "StartEvent"],
                ["critique_joke", "JokeEvent"],
            ],
            "broker_log": [
                '{"__is_pydantic": true, "value": {"_data": {"topic": "duck"}}, "qualified_name": "llama_index.core.workflow.events.StartEvent"}',
                '{"__is_pydantic": true, "value": {"joke": "this is a joke about duck"}, "qualified_name": "tests.agents.jokeflow.JokeEvent"}',
                '{"__is_pydantic": true, "value": {}, "qualified_name": "llama_index.core.workflow.events.StopEvent"}',
            ],
            "event_buffers": {},
            "globals": {},
            "in_progress": {"_done": [], "critique_joke": [], "generate_joke": []},
            "is_running": False,
            "queues": {"_done": "[]", "critique_joke": "[]", "generate_joke": "[]"},
            "stepwise": False,
            "streaming_queue": "[]",
        },
    }
    result = await agent.update_agent_state(thread_id, new_checkpoint)

    history = await agent.get_history(thread_id, None, None)
    assert history is not None
    assert isinstance(history, list)
    assert len(history) == 3
    print(json.dumps(history[2], indent=4, sort_keys=True))
    new_checkpoint["values"]["in_progress"] = {}
    assert history[2]["values"] == new_checkpoint["values"], (
        "Updated checkpoint does not match the expected values"
    )


@pytest.mark.asyncio
async def test_llamaindex_astream_with_interrupt():
    expected_run_1 = [
        {
            "joke": "this is a joke about pirates",
            "first_question": "What is your review about the Joke 'this is a joke about pirates'?",
            "needs_answer": True,
        }
    ]
    expected_run_2 = [
        {},
        {
            "this is a joke about pirates": "this is a joke about pirates",
            "review": "this is a review for the joke: this is a joke about pirates\nReceived human answer: user_value",
        },
    ]
    w = JokeReviewer(timeout=60, verbose=False)

    manifest_path = "tests/agents/jokereviewer_manifest.json"
    manifest = _read_manifest(manifest_path)
    assert manifest

    adapter = LlamaIndexAdapter()  # Replace with actual adapter initialization
    agent = adapter.load_agent(
        agent=w,
        manifest=manifest.extensions[0].data.deployment,
        set_thread_persistance_flag=DB.set_persist_threads,
    )
    assert isinstance(agent, LlamaIndexAgent)

    thread_id = str(uuid4())
    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config=None,
        interrupt=Interrupt(
            event="interrupt_event",
            name="first_interrupt",
            ai_data={"key": "value"},
        ),
    )

    print("First run with interrupt")
    events = []
    async for result in agent.astream(new_run):
        events.append(result.data)
        if (key in result.data for key in ["joke", "first_question", "needs_answer"]):
            # this is the FirstInterruptEvent, in dict form
            break
    assert len(events) == len(expected_run_1), (
        "Unexpected number of events generated during the run"
    )
    for i, event in enumerate(events):
        assert event == expected_run_1[i], (
            f"Event {i} does not match expected value: {event} != {expected_run_1[i]}"
        )

    new_run = Run(
        agent_id=MOCK_AGENT_ID,
        input=MOCK_RUN_INPUT,
        thread_id=thread_id,
        config=None,
        interrupt=Interrupt(
            event="interrupt_event",
            name="first_interrupt",
            ai_data={"key": "value"},
            user_data={"answer": "user_value"},
        ),
    )

    print("Second run")
    events = []
    async for result in agent.astream(new_run):
        events.append(result.data)

    assert len(events) == len(expected_run_2), (
        "Unexpected number of events generated during the run"
    )
    for i, event in enumerate(events):
        assert event == expected_run_2[i], (
            f"Event {i} does not match expected value: {event} != {expected_run_2[i]}"
        )
