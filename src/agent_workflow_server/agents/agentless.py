# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import json
import logging
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from jinja2.sandbox import SandboxedEnvironment
from openai import AsyncAzureOpenAI
from pydantic import BaseModel, Field, RootModel, model_validator
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
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

SupportedModelName = Union[
    KnownModelName,
    Literal[
        "azure:gpt-4o-mini",
        "azure:gpt-4o",
        "azure:gpt-4",
    ],
]


class AgentlessModelArgs(TypedDict, total=False):
    base_url: str
    api_version: str
    azure_endpoint: str
    azure_ad_token: str
    project: str
    organization: str


class AgentlessModelSettings(TypedDict, total=False):
    max_tokens: int
    temperature: float
    top_p: float
    parallel_tool_calls: bool
    seed: int
    presence_penalty: float
    frequency_penalty: float
    logit_bias: dict[str, int]


class AgentlessMessage(BaseModel):
    role: Literal["user", "system", "assistant"] = Field(
        default="user",
    )
    content: str


AgentlessMessageList = RootModel[List[AgentlessMessage]]


class AgentlessAgentConfig(BaseModel):
    models: dict[str, AgentlessModelArgs] = Field(
        default={"azure:gpt-4o-mini": AgentlessModelArgs()},
        description="LLM configuration to use.",
    )
    message_templates: List[AgentlessMessage] = Field(
        max_length=4096,
        default=[],
        description="Prompts used with LLM service.",
    )
    default_model: Optional[str] = Field(
        default="azure:gpt-4o-mini",
        description="Default arguments to LLM completion function by configured model.",
    )
    default_model_settings: dict[str, AgentlessModelSettings] = Field(
        default={"azure:gpt-4o-mini": AgentlessModelSettings(seed=42, temperature=0.8)},
        description="Default LLM configuration to use.",
    )

    @model_validator(mode="after")
    def _validate_obj(self) -> "AgentlessAgentConfig":
        if self.models and self.default_model not in self.models:
            raise ValueError(
                f"default model {self.default_model} not present in configured models"
            )
        # Fill out defaults to eliminate need for checking.
        for model_name in self.models.keys():
            if model_name not in self.default_model_settings:
                self.default_model_settings[model_name] = AgentlessModelSettings()

        return self


class AgentlessRunConfig(BaseModel):
    model_settings: Optional[AgentlessModelSettings] = Field(
        default=None,
        description="Specific arguments for LLM transformation.",
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model out of those configured to handle request.",
    )


class AgentlessRunInput(BaseModel):
    context: Dict[str, str] = Field(
        default={},
        description="Context used for message template rendering.",
    )
    message_templates: List[AgentlessMessage] = Field(
        max_length=4096,
        default=[],
        description="Prompts used with LLM service.",
    )


class AgentlessRunOutput(BaseModel):
    messages: List[AgentlessMessage] = Field(
        max_length=4096,
        default=[],
        description="Prompts used with LLM service.",
    )


def get_supported_agent(
    model_name: SupportedModelName,
    model_args: Dict[str, Any] = {},
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


class Agentless:
    def __init__(self, config: AgentlessAgentConfig):
        self.agent_config = config
        self.jinja_env_async = SandboxedEnvironment(
            loader=None,
            enable_async=True,
            autoescape=False,
        )

    async def ainvoke(
        self, input: AgentlessRunInput, config: AgentlessRunConfig
    ) -> AgentlessRunOutput:
        # Concat agent-wide message prefix with supplied template
        # and render with supplied context
        llm_messages = AgentlessMessageList.model_construct(self.agent_config.message_templates + input.message_templates)
        llm_messages_json = llm_messages.model_dump_json()
        msgs_template = self.jinja_env_async.from_string(llm_messages_json)
        rendered_msgs = await msgs_template.render_async(input.context)
        final_msgs = json.loads(rendered_msgs)
        logger.debug("agentless agent rendered messages: {rendered_msgs}")

        user_prompt, message_history = self._convert_prompts(final_msgs)

        agent = self._get_agent(config)
        response = await agent.run(
            user_prompt,
            model_settings=self._get_model_settings(config),
            message_history=message_history,
        )

        return_msgs = AgentlessMessageList.model_validate(final_msgs)
        return_msgs.append(AgentlessMessage(role="assistant", content=response.data))

        logger.debug(f"agentless agent return messages: {return_msgs.model_dump_json()}")
        return return_msgs

    def _get_model_settings(self, config: AgentlessRunConfig):
        if hasattr(config, "model") and config.model is not None:
            model_name = config.model
        else:
            model_name = self.config.default_model

        if model_name not in self.config.models:
            raise ValueError(f"requested model {model_name} not found")
        elif hasattr(config, "model_settings") and config.model_settings is not None:
            model_settings = self.config.default_model_settings[model_name].copy()
            model_settings.update(config.model_settings)
            return model_settings
        else:
            return self.config.default_model_settings[model_name]

    def _get_agent(self, config: AgentlessRunConfig) -> Agent:
        if hasattr(config, "model") and config.model is not None:
            model_name = config.model
        else:
            model_name = self.agent_config.default_model

        if model_name not in self.agent_config.models:
            raise ValueError(f"requested model {model_name} not found")

        return get_supported_agent(
            model_name,
            model_args=self.agent_config.models[model_name],
            system_prompt=self.agent_config.system_prompt,
        )

    def _convert_prompts(
        self, messages: List[AgentlessMessage]
    ) -> Tuple[str, List[ModelMessage]]:
        user_prompt = ""
        message_history = []

        for msg in messages:
            if msg.role == "user":
                user_prompt = msg.content
                message_history.append(
                    ModelRequest(parts=[UserPromptPart(content=user_prompt)])
                )
            elif msg.role == "assistant":
                content = msg.content
                message_history.append(ModelResponse(parts=[TextPart(content=content)]))
            elif msg.role == "system":
                logger.error("ignoring user supplied system message type")

        return (user_prompt, message_history)
