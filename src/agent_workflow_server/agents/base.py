# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, List, Optional

from agent_workflow_server.generated.manifest.models.agent_manifest import AgentManifest
from agent_workflow_server.services.message import Message
from agent_workflow_server.services.thread_state import ThreadState
from agent_workflow_server.storage.models import Run


class ThreadsNotSupportedError(Exception):
    """Exception raised when threads are not supported by the agent."""

    pass


class BaseAgent(ABC):
    @abstractmethod
    async def astream(self, run: Run) -> AsyncGenerator[Message, None]:
        """Invokes the agent with the given `Run` and streams (returns) `Message`s asynchronously.
        The last `Message` includes the final result."""
        pass

    @abstractmethod
    async def get_agent_state(self, thread_id: str) -> Optional[ThreadState]:
        """Returns the thread state associated with the agent."""
        pass

    @abstractmethod
    async def get_history(
        self, thread_id: str, limit: int, before: int
    ) -> List[ThreadState]:
        """Returns the history of the thread associated with the agent."""
        pass

    @abstractmethod
    async def update_agent_state(
        self, thread_id: str, state: ThreadState
    ) -> Optional[ThreadState]:
        """Updates the thread state associated with the agent."""
        pass


class BaseAdapter(ABC):
    @abstractmethod
    def load_agent(
        self,
        agent: Any,
        manifest: AgentManifest,
        set_thread_persistance_flag: Optional[callable] = None,
    ) -> Optional[BaseAgent]:
        """Checks the type of the agent and if it is supported, returns an instance of the agent."""
        pass
