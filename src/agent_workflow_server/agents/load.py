import importlib.util
import json
import logging
import os
import pkgutil
from typing import Dict, List, NamedTuple

import agent_workflow_server.agents.adapters
from agent_workflow_server.generated.models.agent import Agent
from agent_workflow_server.generated.models.agent_acp_descriptor import (
    AgentACPDescriptor,
)
from agent_workflow_server.generated.models.agent_search_request import (
    AgentSearchRequest,
)

from .base import BaseAdapter, BaseAgent

logger = logging.getLogger(__name__)


class AgentInfo(NamedTuple):
    agent: BaseAgent
    manifest: AgentACPDescriptor


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
                print(f"Could not import {module_path}: {e}")

    return adapters


AGENTS: Dict[str, AgentInfo] = {}
ADAPTERS = _load_adapters()


def _read_manifest(path: str) -> AgentACPDescriptor:
    if os.path.isfile(path):
        with open(path, "r") as file:
            manifest_data = json.load(file)
            # print full path
            logger.info(f"Loaded Agent Manifest from {os.path.abspath(path)}")
        return AgentACPDescriptor(**manifest_data)


def _resolve_agent(name: str, path: str) -> AgentInfo:
    module_or_file, export_symbol = path.split(":", 1)
    if not os.path.isfile(module_or_file):
        # It's a module (name), try to import it
        module_name = module_or_file
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            raise ImportError(
                f"""Failed to load agent module {module_name}. \
Check if it\'s installed and that module name in 'AGENTS_REF' env variable is correct."""
            )
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

    # Check if the variable exists in the module
    if hasattr(module, export_symbol):
        resolved = getattr(module, export_symbol)

        agent = None
        for adapter in ADAPTERS:
            agent = adapter.load_agent(resolved)
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

    # Load manifest. Check in paths below (in order)
    manifest_paths = [
        os.path.join(os.path.dirname(module.__file__), "manifest.json"),
        os.environ.get("AGENT_MANIFEST_PATH", "manifest.json") or "manifest.json",
    ]

    for manifest_path in manifest_paths:
        manifest = _read_manifest(manifest_path)
        if manifest:
            break
    else:
        raise ImportError("Failed to load agent manifest")

    logger.info(f"Loaded Agent from {module.__file__}")
    logger.info(f"Agent Type: {type(agent).__name__}")

    return AgentInfo(agent=agent, manifest=manifest)


def load_agents():
    # Simulate loading the config from environment variable

    try:
        config: Dict[str, str] = json.loads(os.getenv("AGENTS_REF", {}))
    except json.JSONDecodeError:
        raise ValueError("""Invalid format for AGENTS_REF environment variable. \
Must be a dictionary of agent_id -> module:var pairs. \
Example: {"agent1": "agent1_module:agent1_var", "agent2": "agent2_module:agent2_var"}""")
    for agent_id, agent_path in config.items():
        try:
            agent = _resolve_agent(agent_id, agent_path)
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

    return Agent(agent_id=agent_id, metadata=AGENTS[agent_id].manifest.metadata)


def get_agent_from_agent_info(agent_id: str, agent_info: AgentInfo) -> Agent:
    if agent_id not in AGENTS:
        raise ValueError(f'Agent "{agent_id}" not found')

    return Agent(agent_id=agent_id, metadata=agent_info.manifest.metadata)


def search_agents(search_request: AgentSearchRequest) -> List[Agent]:
    if not search_request.name and not search_request.version:
        raise ValueError("At least one of 'name' or 'version' must be provided")

    return [
        Agent(agent_id=agent_id, metadata=agent.manifest.metadata)
        for agent_id, agent in AGENTS.items()
        if (
            not search_request.name
            or search_request.name == agent.manifest.metadata.ref.name
        )
        and (
            not search_request.version
            or search_request.version == agent.manifest.metadata.ref.version
        )
    ]
