# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, Optional

from agent_workflow_server.services.message import Message
from agent_workflow_server.storage.models import Config


class BaseAgent(ABC):
    @abstractmethod
    async def astream(
        self, input: Optional[Dict[str, Any]], config: Optional[Config]
    ) -> AsyncGenerator[Message, None]:
        """Invokes the agent with the given input and configuration and streams (returns) `Message`s asynchronously.
        The last `Message` includes the final result."""
        pass


class BaseAdapter(ABC):
    @abstractmethod
    def load_agent(self, agent: Any) -> Optional[BaseAgent]:
        """Checks the type of the agent and if it is supported, returns an instance of the agent."""
        pass
