# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
from typing import Optional, List, Dict
from pydantic import Field

from pydantic import BaseModel


class Agentless:
    def __init__(self, manifest):
        self.manifest = manifest

    async def astream(self, input, config): ...

    # Placeholder for the actual implementation


class AgentlessConfig(BaseModel):
    system_prompt: str
