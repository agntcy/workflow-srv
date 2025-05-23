# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
import logging
import os
import pkgutil
from typing import Any, Dict, Hashable, List, Mapping, NamedTuple, Optional

import agent_workflow_server.agents.adapters
from agent_workflow_server.agents.oas_generator import generate_agent_oapi
from agent_workflow_server.generated.manifest.models.agent_deployment import (
    AgentDeployment,
)
from agent_workflow_server.generated.manifest.models.agent_manifest import AgentManifest
from agent_workflow_server.generated.models.agent import Agent
from agent_workflow_server.generated.models.agent_acp_descriptor import (
    AgentACPDescriptor,
)
from agent_workflow_server.generated.models.agent_acp_spec import AgentACPSpec
from agent_workflow_server.generated.models.agent_metadata import AgentMetadata
from agent_workflow_server.generated.models.agent_ref import AgentRef
from agent_workflow_server.generated.models.agent_search_request import (
    AgentSearchRequest,
)
from agent_workflow_server.storage.storage import DB

from .base import BaseAdapter, BaseAgent

logger = logging.getLogger(__name__)


def _make_acp_descriptor(manifest: AgentManifest) -> AgentACPDescriptor:
    """Create an AgentACPDescriptor from a AgentManifest"""
    if not manifest.extensions or len(manifest.extensions) == 0:
        raise ValueError(
            "Manifest does not contain any extensions. Cannot create ACP descriptor."
        )
    return AgentACPDescriptor(
        metadata=AgentMetadata(
            ref=AgentRef(
                name=manifest.name,
                version=manifest.version,
                url=manifest.locators[0].url,
            ),
            description=manifest.description,
        ),
        specs=AgentACPSpec.model_validate(manifest.extensions[0].data.acp.model_dump()),
    )


class AgentInfo(NamedTuple):
    agent: BaseAgent
    acp_descriptor: AgentACPDescriptor
    schema: Mapping[Hashable, Any]
    deployment: AgentDeployment


def _load_adapters() -> List[BaseAdapter]:
    adapters = []
    package = agent_workflow_server.agents.adapters
    for _, module_name, _ in pkgutil.iter_modules(package.__path__):
        if not module_name.startswith("_"):
            # Use the package's name to construct the full module path
            module_path = f"{package.__name__}.{module_name}"
            try:
                module = importlib.import_module(module_path)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseAdapter)
                        and attr is not BaseAdapter
                    ):
                        adapters.append(attr())
            except ImportError as e:
                logger.error(f"Could not import adapter from {module_path}: {e}")

    return adapters


AGENTS: Dict[str, AgentInfo] = {}
ADAPTERS = _load_adapters()


def _read_manifest(path: str):
    if os.path.isfile(path):
        with open(path, "r") as file:
            manifest_data = json.load(file)
            manifest = AgentManifest.model_validate(manifest_data)
            # print full path
            logger.info(f"Loaded Agent Manifest from {os.path.abspath(path)}")
        return _make_acp_descriptor(manifest), manifest.extensions[0].data.deployment

    return None, None


def _resolve_agent(
    name: str, path: str, add_manifest_paths: List[str] = []
) -> AgentInfo:
    if ":" not in path:
        raise ValueError(
            f"""Invalid format for AGENTS_REF environment variable. \
Value must be a module:var pair. \
Example: "agent1_module:agent1_var" or "path/to/file.py:agent1_var"
Got: {path}"""
        )

    module_or_file, export_symbol = path.split(":", 1)
    if not os.path.isfile(module_or_file):
        # It's a module (name), try to import it
        module_name = module_or_file
        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            if any(part in str(e) for part in module_name.split(".")):
                raise ImportError(
                    f"""Failed to load agent module {module_name}. \
Check that it is installed and that the module name in 'AGENTS_REF' env variable is correct."""
                ) from e
            else:
                raise e
    else:
        # It's a path to a file, try to load it as a module
        file = module_or_file
        spec = importlib.util.spec_from_file_location(name, file)
        if spec is None:
            raise ImportError(
                f"""Failed to load agent: {file} is not a valid Python file. \
Check that file path in 'AGENTS_REF' env variable is correct."""
            )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

    # Load manifest. Check in paths below (in order)
    manifest_paths = [
        os.path.join(os.path.dirname(module.__file__), "manifest.json"),
    ] + add_manifest_paths

    for manifest_path in manifest_paths:
        acp_descriptor, deployment = _read_manifest(manifest_path)
        if acp_descriptor and deployment:
            break
    else:
        raise ImportError(
            f"Failed to load agent manifest from any of the paths: {manifest_paths}"
        )

    try:
        schema = generate_agent_oapi(acp_descriptor, name)
    except Exception as e:
        raise ImportError("Failed to generate OAPI schema:", e)

    # Check if the variable exists in the module
    if hasattr(module, export_symbol):
        resolved = getattr(module, export_symbol)

        agent = None
        for adapter in ADAPTERS:
            agent = adapter.load_agent(resolved, deployment, DB.set_persist_threads)
            if agent is not None:
                break
        else:
            raise ImportError(
                f"""Failed to load agent: Could not find adapter for {type(resolved).__name__}"""
            )
    else:
        raise ImportError(
            f"""Failed to load agent: {export_symbol} not found in {module.__name__}. \
Check that the module name and export symbol in 'AGENTS_REF' env variable are correct."""
        )

    logger.info(f"Loaded Agent from {module.__file__}")
    logger.info(f"Agent Type: {type(agent).__name__}")

    return AgentInfo(
        agent=agent, acp_descriptor=acp_descriptor, deployment=deployment, schema=schema
    )


def load_agents(agents_ref: Optional[str] = None, add_manifest_paths: List[str] = []):
    try:
        config: Dict[str, str] = json.loads(agents_ref) if agents_ref else {}
    except json.JSONDecodeError:
        raise ValueError("""Invalid format for AGENTS_REF environment variable. \
Must be a dictionary of agent_id -> module:var pairs. \
Example: {"agent1": "agent1_module:agent1_var", "agent2": "agent2_module:agent2_var"}""")
    for agent_id, agent_path in config.items():
        try:
            agent = _resolve_agent(agent_id, agent_path, add_manifest_paths)
            AGENTS[agent_id] = agent
            logger.info(f"Registered Agent: '{agent_id}'", {"agent_id": agent_id})
        except Exception as e:
            logger.error(e)
            raise Exception(e)


def get_agent_info(agent_id: str) -> AgentInfo:
    if agent_id not in AGENTS:
        raise ValueError(f'Agent "{agent_id}" not found')

    return AGENTS[agent_id]


def get_agent(agent_id: str) -> Agent:
    if agent_id not in AGENTS:
        raise ValueError(f'Agent "{agent_id}" not found')

    return Agent(agent_id=agent_id, metadata=AGENTS[agent_id].acp_descriptor.metadata)


def get_default_agent() -> Agent:
    if len(AGENTS) == 0:
        raise ValueError("No agents available")
    agent_id = next(iter(AGENTS))
    return Agent(agent_id=agent_id, metadata=AGENTS[agent_id].acp_descriptor.metadata)


def get_agent_from_agent_info(agent_id: str, agent_info: AgentInfo) -> Agent:
    if agent_id not in AGENTS:
        raise ValueError(f'Agent "{agent_id}" not found')

    return Agent(agent_id=agent_id, metadata=agent_info.acp_descriptor.metadata)


def search_for_agents(search_request: AgentSearchRequest) -> List[Agent]:
    if not search_request.name and not search_request.version:
        raise ValueError("At least one of 'name' or 'version' must be provided")

    return [
        Agent(agent_id=agent_id, metadata=agent.acp_descriptor.metadata)
        for agent_id, agent in AGENTS.items()
        if (
            not search_request.name
            or search_request.name == agent.acp_descriptor.metadata.ref.name
        )
        and (
            not search_request.version
            or search_request.version == agent.acp_descriptor.metadata.ref.version
        )
    ]


def get_agent_openapi_schema(agent_id: str) -> str:
    if agent_id not in AGENTS:
        raise ValueError(f'Agent "{agent_id}" not found')

    return json.dumps(AGENTS[agent_id].schema, indent=2)
