# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Any, Literal, Optional, Union, List, Dict

from openai import AsyncAzureOpenAI
from pydantic import Field, model_validator, BaseModel
from pydantic_ai import Agent
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models import KnownModelName
from pydantic_ai.models.openai import OpenAIModel


logger = logging.getLogger(__name__)


class AgentIOModelArgs(BaseModel):
    base_url: str
    api_version: str
    azure_endpoint: str
    azure_ad_token: str
    project: str
    organization: str


class AgentModelSettings(BaseModel):
    max_tokens: int
    temperature: float
    top_p: float
    parallel_tool_calls: bool
    seed: int
    presence_penalty: float
    frequency_penalty: float
    logit_bias: dict[str, int]


class PydanticAIAgentInput(BaseModel):
    model_settings: Optional[AgentModelSettings] = Field(
        default=None,
        description="Specific arguments for LLM transformation.",
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model out of those configured to handle request.",
    )
    messages: List[Dict[str,str]] = Field(
        None,
        description="Default user message template. This can be overridden by the message request.",
    )


class PydanticAIAgentConfig(BaseModel):
    models: dict[str, AgentIOModelArgs] = Field(
        default={"azure:gpt-4o-mini": AgentIOModelArgs()},
        description="LLM configuration to use.",
    )
    system_prompt: str = Field(
        max_length=4096,
        description="System prompt used with LLM service.",
    )
    default_model: Optional[str] = Field(
        default="azure:gpt-4o-mini",
        description="Default arguments to LLM completion function by configured model.",
    )
    default_model_settings: dict[str, AgentModelSettings] = Field(
        default={"azure:gpt-4o-mini": AgentModelSettings(seed=42, temperature=0.8)},
        description="Default LLM configuration to use.",
    )

    @model_validator(mode="after")
    def _validate_obj(self) -> "PydanticAIAgentConfig":
        if self.models and self.default_model not in self.models:
            raise ValueError(
                f"default model {self.default_model} not present in configured models"
            )
        # Fill out defaults to eliminate need for checking.
        for model_name in self.models.keys():
            if model_name not in self.default_model_settings:
                self.default_model_settings[model_name] = AgentModelSettings()

        return self


SupportedModelName = Union[
    KnownModelName,
    Literal[
        "azure:gpt-4o-mini",
        "azure:gpt-4o",
        "azure:gpt-4",
    ],
]


def get_supported_agent(
    model_name: SupportedModelName,
    model_args: dict[str, Any] = {},
    **kwargs,
) -> Agent:
    """
    Creates and returns an `Agent` instance for the given model.

    Args:
        model_name (SupportedModelName): The name of the model to be used.
            If the name starts with "azure:", an `AsyncAzureOpenAI` client is used.
        model_args (dict[str, Any], optional): Additional arguments for model
            initialization. Defaults to an empty dictionary.
        **kwargs: Additional keyword arguments passed to the `Agent` constructor.

    Returns:
        Agent: An instance of the `Agent` class configured with the specified model.

    Notes:
        - The `pydantic-ai` package does not currently pass `model_args` to the
          inferred model in the constructor, but this behavior might change in
          the future.
    """
    if model_name.startswith("azure:"):
        client = AsyncAzureOpenAI(**model_args)
        model = OpenAIModel(model_name[6:], openai_client=client)
        return Agent(model, **kwargs)

    return Agent(model_name, **kwargs)


class PydanticAIIOAgent():
    def __init__(
        self,
        config: PydanticAIAgentConfig,
    ):
        self.config = config
    
    def _get_model_settings(self, input: PydanticAIAgentInput):
        if hasattr(input, "model") and input.model is not None:
            model_name = input.model
        else:
            model_name = self.config.default_model

        if model_name not in self.config.models:
            raise ValueError(f"requested model {model_name} not found")
        elif hasattr(input, "model_settings") and input.model_settings is not None:
            model_settings = self.config.default_model_settings[model_name].copy()
            model_settings.update(input.model_settings)
            return model_settings
        else:
            return self.config.default_model_settings[model_name]

    def _get_agent(
        self, input: PydanticAIAgentInput, system_prompt: str
    ) -> Agent:
        if hasattr(input, "model") and input.model is not None:
            model_name = input.model
        else:
            model_name = self.config.default_model

        if model_name not in self.config.models:
            raise ValueError(f"requested model {model_name} not found")

        return get_supported_agent(
            model_name,
            model_args=self.config.models[model_name],
            system_prompt=system_prompt,
        )

    def _convert_prompts(
        self, messages: list[dict[str, str]]
    ) -> tuple[str, list[ModelMessage]]:
        user_prompt = ""
        message_history = []

        for msg in messages:
            role = msg.get("role", "user")

            if role.lower() == "user":
                user_prompt = msg.get("content", "")
                message_history.append(
                    ModelRequest(parts=[UserPromptPart(content=user_prompt)])
                )
            elif role.lower() == "assistant":
                content = msg.get("content", "")
                message_history.append(ModelResponse(parts=[TextPart(content=content)]))
            else:
                logger.warning("ignoring unknown message type: {role}")

        return (user_prompt, message_history)

    def invoke(
        self,
        input: PydanticAIAgentInput,
        **kwargs,
    ) -> str:
        user_prompt, message_history = self._convert_prompts(input.messages)

        agent = self._get_agent(input, self.config.system_prompt)
        response = agent.run_sync(
            user_prompt,
            model_settings=self._get_model_settings(input),
            message_history=message_history,
        )
        return response.data

    async def ainvoke(
        self,
        input: PydanticAIAgentInput,
        **kwargs,
    ) -> str:
        user_prompt, message_history = self._convert_prompts(input.messages)

        agent = self._get_agent(input, self.config.system_prompt)
        response = await agent.run(
            user_prompt,
            model_settings=self._get_model_settings(input),
            message_history=message_history,
        )
        return response.data
