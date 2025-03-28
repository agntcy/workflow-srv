# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0


import uuid

import pytest

from agent_workflow_server.agents.oas_generator import (
    generate_agent_oapi,
)
from agent_workflow_server.generated.models.agent_acp_descriptor import (
    AgentACPDescriptor,
)
from agent_workflow_server.generated.models.agent_acp_spec import AgentACPSpec
from agent_workflow_server.generated.models.agent_acp_spec_interrupts_inner import (
    AgentACPSpecInterruptsInner,
)
from agent_workflow_server.generated.models.agent_capabilities import AgentCapabilities
from agent_workflow_server.generated.models.agent_metadata import AgentMetadata
from agent_workflow_server.generated.models.agent_ref import AgentRef
from agent_workflow_server.generated.models.streaming_modes import StreamingModes


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
    agent_id = str(uuid.uuid4())
    result = generate_agent_oapi(basic_descriptor, agent_id)

    # Verify basic structure
    assert "openapi" in result
    assert "info" in result
    assert (
        result["info"]["title"]
        == f"ACP Spec for {basic_descriptor.metadata.ref.name}:{basic_descriptor.metadata.ref.version}"
    )
    assert "paths" in result
    assert "components" in result

    # Verify schemas
    schemas = result["components"]["schemas"]
    assert "InputSchema" in schemas
    assert schemas["InputSchema"]["properties"]["test"]["type"] == "string"
    assert "OutputSchema" in schemas
    assert schemas["OutputSchema"]["properties"]["result"]["type"] == "string"
    assert "ConfigSchema" in schemas
    assert schemas["ConfigSchema"]["properties"]["mode"]["type"] == "string"

    # Verify no thread paths exist
    assert "/threads" not in result["paths"]
    assert "/threads/search" not in result["paths"]

    # Verify no streaming endpoints
    assert "/runs/{run_id}/stream" not in result["paths"]

    # Verify no webhook/callback properties
    assert "webhook" not in result["components"]["schemas"]["RunCreate"]["properties"]

    # Verify security schemes
    assert "securitySchemes" in result["components"]
    assert "ApiKeyAuth" in result["components"]["securitySchemes"]
    assert result["components"]["securitySchemes"]["ApiKeyAuth"]["type"] == "apiKey"
    assert result["components"]["securitySchemes"]["ApiKeyAuth"]["in"] == "header"

    # Verify default agent_id is set
    for path in result["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict) and "parameters" in operation:
                for param in operation["parameters"]:
                    if param.get("name") == "agent_id":
                        assert param["schema"]["default"] == agent_id


# Add a new test for full capabilities
@pytest.fixture
def full_descriptor():
    """Create a descriptor with all capabilities enabled"""
    return AgentACPDescriptor(
        metadata=AgentMetadata(
            ref=AgentRef(name="full-agent", version="1.0.0", url=None),
            description="Full capability agent",
        ),
        specs=AgentACPSpec(
            capabilities=AgentCapabilities(
                threads=True,
                interrupts=True,
                callbacks=True,
                streaming=StreamingModes(native=True, custom=False),
            ),
            input={"type": "object", "properties": {"test": {"type": "string"}}},
            output={"type": "object", "properties": {"result": {"type": "string"}}},
            config={"type": "object", "properties": {"mode": {"type": "string"}}},
            thread_state={
                "type": "object",
                "properties": {"status": {"type": "string"}},
            },
            interrupts=[
                AgentACPSpecInterruptsInner(
                    interrupt_type="stop",
                    interrupt_payload={
                        "type": "object",
                        "properties": {"reason": {"type": "string"}},
                    },
                    resume_payload={"type": "object", "properties": {}},
                )
            ],
            custom_streaming_update=None,
        ),
    )


def test_generate_full_spec(full_descriptor):
    """Test generating a spec with all capabilities enabled"""
    agent_id = str(uuid.uuid4())
    result = generate_agent_oapi(full_descriptor, agent_id)

    # Verify thread capabilities
    assert "/threads" in result["paths"]
    assert "/threads/search" in result["paths"]
    assert "ThreadState" in result["components"]["schemas"]
    assert (
        result["components"]["schemas"]["ThreadState"]["properties"]["status"]["type"]
        == "string"
    )

    # Verify streaming capabilities in more detail
    assert "/runs/{run_id}/stream" in result["paths"]
    run_create_schema = result["components"]["schemas"]["RunCreate"]
    assert "properties" in run_create_schema

    # Verify stream_mode property structure
    assert "stream_mode" in run_create_schema["properties"]
    stream_mode_prop = run_create_schema["properties"]["stream_mode"]

    # Verify the anyOf structure
    assert "anyOf" in stream_mode_prop, f"Expected 'anyOf' in {stream_mode_prop}"
    assert isinstance(stream_mode_prop["anyOf"], list)
    assert len(stream_mode_prop["anyOf"]) == 3  # array, single value, or null

    # Verify array option
    array_option = stream_mode_prop["anyOf"][0]
    assert array_option["type"] == "array"
    assert "items" in array_option
    assert array_option["items"]["$ref"] == "#/components/schemas/StreamingMode"

    # Verify single value option
    single_option = stream_mode_prop["anyOf"][1]
    assert single_option["$ref"] == "#/components/schemas/StreamingMode"

    # Verify null option
    null_option = stream_mode_prop["anyOf"][2]
    assert null_option["type"] == "null"

    # Verify metadata
    assert stream_mode_prop["title"] == "Stream Mode"
    assert "description" in stream_mode_prop
    assert stream_mode_prop["default"] is None

    # Verify interrupt capabilities
    assert "/runs/{run_id}/cancel" in result["paths"], (
        f"Expected cancel path, got paths: {list(result['paths'].keys())}"
    )

    # Verify cancel endpoint structure
    cancel_path = result["paths"]["/runs/{run_id}/cancel"]
    assert "post" in cancel_path

    # Verify cancel endpoint details
    cancel_post = cancel_path["post"]
    assert "operationId" in cancel_post
    assert "parameters" in cancel_post
    assert any(param["name"] == "run_id" for param in cancel_post["parameters"])

    # Verify security is applied
    assert "security" in cancel_post
    assert [{"ApiKeyAuth": []}] == cancel_post["security"]

    # Verify responses
    assert "responses" in cancel_post
    assert "204" in cancel_post["responses"], (
        f"Expected 204 response, got: {list(cancel_post['responses'].keys())}"
    )

    # 204 No Content shouldn't have a response body
    assert "content" not in cancel_post["responses"]["204"], (
        "204 responses should not have content"
    )

    # Verify error responses are present
    assert "422" in cancel_post["responses"], "Validation error response missing"
    assert "content" in cancel_post["responses"]["422"]
    assert "application/json" in cancel_post["responses"]["422"]["content"]
    assert (
        cancel_post["responses"]["422"]["content"]["application/json"]["schema"]["$ref"]
        == "#/components/schemas/ErrorResponse"
    )

    # Verify callback capabilities
    assert "webhook" in result["components"]["schemas"]["RunCreate"]["properties"]
