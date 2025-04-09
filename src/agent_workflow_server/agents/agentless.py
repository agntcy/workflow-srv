# Agentless code here

from pydantic import BaseModel


class Agentless:
    async def astream(self, input, config): ...

    # Placeholder for the actual implementation


class AgentlessConfig(BaseModel):
    system_prompt: str
