# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from typing import ClassVar, Dict, List, Tuple  # noqa: F401

from pydantic import Field, StrictStr
from typing import List
from typing_extensions import Annotated
from agent_workflow_server.generated.models.agent import Agent
from agent_workflow_server.generated.models.agent_acp_descriptor import AgentACPDescriptor
from agent_workflow_server.generated.models.agent_search_request import AgentSearchRequest


class BaseAgentsApi:
    subclasses: ClassVar[Tuple] = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        BaseAgentsApi.subclasses = BaseAgentsApi.subclasses + (cls,)
    async def get_acp_descriptor_by_id(
        self,
        agent_id: Annotated[StrictStr, Field(description="The ID of the agent.")],
    ) -> AgentACPDescriptor:
        """Get agent ACP descriptor by agent ID."""
        ...


    async def get_agent_by_id(
        self,
        agent_id: Annotated[StrictStr, Field(description="The ID of the agent.")],
    ) -> Agent:
        """Get an agent by ID."""
        ...


    async def search_agents(
        self,
        agent_search_request: AgentSearchRequest,
    ) -> List[Agent]:
        """Returns a list of agents matching the criteria provided in the request.  This endpoint also functions as the endpoint to list all agents."""
        ...
