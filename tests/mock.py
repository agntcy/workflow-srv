# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
from typing import AsyncGenerator, List, Optional

from agent_workflow_server.agents.base import BaseAdapter, BaseAgent
from agent_workflow_server.generated.manifest.models.agent_manifest import AgentManifest
from agent_workflow_server.services.message import Message
from agent_workflow_server.services.thread_state import ThreadState
from agent_workflow_server.storage.models import Run

# Make sure that this and the one in the .env.test file are the same
MOCK_AGENT_ID = "3f1e2549-5799-4321-91ae-2a4881d55526"

MOCK_RUN_INPUT = {"message": "What's the color of the sky?"}
MOCK_RUN_OUTPUT = {"message": "The color of the sky is blue"}

MOCK_RUN_INPUT_STREAM = {"message": "What's the color of the sky?"}
MOCK_RUN_OUTPUT_STREAM = [
    {"message": "The color of the sky is blue"},
    {"message": "The color of the sky is not white"},
    {"message": "The color of the sky is sky blue, in fact"},
]

MOCK_RUN_INPUT_INTERRUPT = {"message": "Please interrupt"}
MOCK_RUN_EVENT_INTERRUPT = "__mock_interrupt__"
MOCK_RUN_OUTPUT_INTERRUPT = {"interrupt_message": "How can I help you?"}

MOCK_RUN_INPUT_ERROR = {"message": "I don't feel too well."}
MOCK_RUN_OUTPUT_ERROR = 'error input: {"message": "I don\'t feel too well."}'

MOCK_THREAD_ID = "3f1e2549-5799-4321-91ae-2a4881d55526"


class MockAgentImpl: ...


class MockAgent(BaseAgent):
    def __init__(self, agent: MockAgentImpl):
        self.agent = agent

    async def astream(self, run: Run) -> AsyncGenerator[Message, None]:
        if run["input"] == MOCK_RUN_INPUT or (
            run.get("interrupt") is not None
            and run["interrupt"].get("user_data") == MOCK_RUN_INPUT
        ):
            await asyncio.sleep(3)
            yield Message(type="message", data=MOCK_RUN_OUTPUT)
        elif run["input"] == MOCK_RUN_INPUT_INTERRUPT:
            yield Message(
                type="interrupt",
                event=MOCK_RUN_EVENT_INTERRUPT,
                data=MOCK_RUN_OUTPUT_INTERRUPT,
            )
        elif run["input"] == MOCK_RUN_INPUT_STREAM:
            async for data in MOCK_RUN_OUTPUT_STREAM:
                yield Message(type="message", data=data)
        elif run["input"] == MOCK_RUN_INPUT_ERROR:
            raise ValueError("error input: " + json.dumps(run["input"]))

    # Mock get_agent_state
    async def get_agent_state(self, thread_id: str) -> Optional[ThreadState]:
        if thread_id == MOCK_THREAD_ID:
            return ThreadState(
                thread_id=MOCK_THREAD_ID,
                state={"message": "The color of the sky is blue"},
                created_at=MOCK_RUN_INPUT["created_at"],
                updated_at=MOCK_RUN_INPUT["updated_at"],
            )
        return None

    # Mock get_history
    async def get_history(
        self, thread_id: str, limit: int, before: int
    ) -> List[ThreadState]:
        if thread_id == MOCK_THREAD_ID:
            return [
                ThreadState(
                    thread_id=MOCK_THREAD_ID,
                    state={"message": "The color of the sky is blue"},
                    created_at=MOCK_RUN_INPUT["created_at"],
                    updated_at=MOCK_RUN_INPUT["updated_at"],
                )
            ]
        return []

    # Mock update_agent_state
    async def update_agent_state(
        self, thread_id: str, state: ThreadState
    ) -> Optional[ThreadState]:
        return None


class MockAdapter(BaseAdapter):
    def load_agent(
        self,
        agent: object,
        manifest: AgentManifest,
        set_thread_persistance_flag: Optional[callable] = None,
    ):
        if isinstance(agent, MockAgentImpl):
            return MockAgent(agent)


mock_agent = MockAgentImpl()
