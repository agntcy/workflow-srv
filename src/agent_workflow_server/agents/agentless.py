# Agentless code here

from pydantic import BaseModel


class Agentless:
    def __init__(self, manifest):
        self.manifest = manifest

    async def astream(self, input, config): ...

    # Placeholder for the actual implementation


class AgentlessConfig(BaseModel):
    system_prompt: str
