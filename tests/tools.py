# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import os

from agent_workflow_server.generated.manifest.models.agent_manifest import AgentManifest

logger = logging.getLogger(__name__)


def _read_manifest(path: str) -> AgentManifest:
    if os.path.isfile(path):
        with open(path, "r") as file:
            try:
                manifest_data = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON format in manifest file: {path}. Error: {e}"
                )
            # print full path
            logger.info(f"Loaded Agent Manifest from {os.path.abspath(path)}")
        return AgentManifest.model_validate(manifest_data)
    return None
