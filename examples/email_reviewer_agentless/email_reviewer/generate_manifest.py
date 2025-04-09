# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
from agent_workflow_server.agents.agentless import (
    AgentlessAgentConfig,
    AgentlessRunConfig,
    AgentlessRunInput,
    AgentlessRunOutput,
    AgentlessMessage
)

from agntcy_acp.manifest import (
    AgentManifest,
    AgentDeployment,
    DeploymentOptions,
    LlamaIndexConfig,
    EnvVar,
    AgentMetadata,
    AgentACPSpec,
    AgentRef,
    Capabilities,
    SourceCodeDeployment
)


manifest = AgentManifest(
    metadata=AgentMetadata(
        ref=AgentRef(name="org.agntcy.mail_reviewer_agentless", version="0.0.1", url=None),
        description="Review emails"),
    specs=AgentACPSpec(
        input=AgentlessRunInput.model_json_schema(),
        output=AgentlessRunOutput.model_json_schema(),
        config=AgentlessRunConfig.model_json_schema(),
        capabilities=Capabilities(
            threads=False,
            callbacks=False,
            interrupts=False,
            streaming=None
        ),
        custom_streaming_update=None,
        thread_state=None,
        interrupts=None
    ),
    deployment=AgentDeployment(
        deployment_options=[
        ],
        env_vars=[EnvVar(name="AZURE_OPENAI_API_KEY", desc="Azure key for the OpenAI service")],
        dependencies=[]
    )
)


EMAIL_REVIEWER_SYSTEM_PROMPT = "You are an email reviewer assistant, in charge of reviewing an email"

EMAIL_REVIEWER_USER_PROMPT = """Your tasks are:
1) Check whether the provided email has no writing errors
2) Check whether the provided email matches the target audience
3) If the email has writing errors or does not match the target audience below, correct the email.

The target audience:
{{target_audience}}

The email:
{{email}}
"""


agentless_config = AgentlessAgentConfig(
    message_templates=[
        AgentlessMessage(
            role="system",
            content=EMAIL_REVIEWER_SYSTEM_PROMPT
        ),
        AgentlessMessage(
            role="system",
            content=EMAIL_REVIEWER_USER_PROMPT
        ),
    ]
)


mdict = manifest.model_dump()
mdict["deployment"]["deployment_options"].append(
{
    "type": "source_code",
    "name": "source_code_local",
    "framework_config": {
        "framework_type": "agentless",
        "config": agentless_config.model_dump(),
    }
})

with open(f"{Path(__file__).parent}/../deploy/email_reviewer_agentless.json", "w") as f:
    f.write(json.dumps(mdict,
        indent=2
    ))