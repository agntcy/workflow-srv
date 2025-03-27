# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0


import pytest

from agent_workflow_server.agents.oas_generator import (
    generate_agent_oapi,
)
from agent_workflow_server.generated.models.agent_acp_descriptor import (
    AgentACPDescriptor,
)
from agent_workflow_server.generated.models.agent_acp_spec import AgentACPSpec
from agent_workflow_server.generated.models.agent_capabilities import AgentCapabilities
from agent_workflow_server.generated.models.agent_metadata import AgentMetadata
from agent_workflow_server.generated.models.agent_ref import AgentRef


@pytest.fixture
def basic_descriptor():
    """Create a basic descriptor for testing"""
    return AgentACPDescriptor(
        metadata=AgentMetadata(
            ref=AgentRef(name="test-agent", version="1.0.0", url=None),
            description="Test agent description",
        ),
        specs=AgentACPSpec(
            capabilities=AgentCapabilities(
                threads=False, interrupts=False, callbacks=False, streaming=None
            ),
            input={"type": "object", "properties": {"test": {"type": "string"}}},
            output={"type": "object", "properties": {"result": {"type": "string"}}},
            config={"type": "object", "properties": {"mode": {"type": "string"}}},
            thread_state=None,
            interrupts=[],
            custom_streaming_update=None,
        ),
    )


def test_generate_basic_spec(basic_descriptor):
    """Test generating a basic spec with minimal capabilities"""
    result = generate_agent_oapi(basic_descriptor)

    # Verify basic structure
    assert "openapi" in result
    assert "info" in result
    assert "paths" in result
    assert "components" in result

    # Verify schemas
    schemas = result["components"]["schemas"]
    assert "InputSchema" in schemas
    assert "OutputSchema" in schemas
    assert "ConfigSchema" in schemas

    # Verify no thread paths exist
    assert "/threads" not in result["paths"]
    assert "/threads/search" not in result["paths"]

    # Verify no streaming endpoints
    assert "/runs/{run_id}/stream" not in result["paths"]
