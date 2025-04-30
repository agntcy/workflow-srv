# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from unittest import mock

import pytest

from agent_workflow_server.generated.models.run_create_stateful import RunCreateStateful
from agent_workflow_server.generated.models.run_create_stateless import (
    RunCreateStateless,
)
from agent_workflow_server.services.validation import (
    InvalidFormatException,
    validate_output,
    validate_run_create,
)


@pytest.fixture
def mock_get_agent_schemas():
    with mock.patch("agent_workflow_server.services.validation.get_agent_schemas") as m:
        yield m


@pytest.mark.parametrize(
    "output, schema, should_raise",
    [
        (
            {"result": "success"},
            {"type": "object", "properties": {"result": {"type": "string"}}},
            False,
        ),
        (
            {"result": 123},
            {"type": "object", "properties": {"result": {"type": "string"}}},
            True,
        ),
        (None, {"type": "object"}, False),  # None output should not validate
        ({"data": "test"}, {"type": "object", "required": ["result"]}, True),
    ],
)
def test_validate_output(mock_get_agent_schemas, output, schema, should_raise):
    agent_id = "test-agent-id"
    run_id = "test-run-id"

    mock_get_agent_schemas.return_value = {"input": {}, "output": schema, "config": {}}

    if should_raise:
        with pytest.raises(InvalidFormatException):
            validate_output(run_id, agent_id, output)
    else:
        validate_output(run_id, agent_id, output)  # Should not raise


def test_validate_output_agent_not_found():
    run_id = "test-run-id"
    agent_id = "non-existent-agent"
    output = {"result": "test"}

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.side_effect = ValueError(f"Agent {agent_id} not found")

        with pytest.raises(ValueError, match=f"Agent {agent_id} not found"):
            validate_output(run_id, agent_id, output)


@pytest.fixture
def mock_get_agent_schemas_for_run_create():
    with mock.patch("agent_workflow_server.services.validation.get_agent_schemas") as m:
        yield m


def test_validate_run_create_valid():
    run_create = RunCreateStateless(
        agent_id="test-agent",
        input={"query": "test"},
        config={"configurable": {"param": "value"}},
    )

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.return_value = {
            "input": {"type": "object", "properties": {"query": {"type": "string"}}},
            "output": {},
            "config": {"type": "object", "properties": {"param": {"type": "string"}}},
        }

        result = validate_run_create(run_create)
        assert result == run_create  # Should return the validated object


def test_validate_run_create_missing_required_input():
    run_create = RunCreateStateful(
        agent_id="test-agent", input=None, config={"configurable": {"param": "value"}}
    )

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.return_value = {
            "input": {"type": "object"},  # Input schema exists but input is None
            "output": {},
            "config": {"type": "object"},
        }

        with pytest.raises(
            InvalidFormatException, match='"input" is required for this agent'
        ):
            validate_run_create(run_create)


def test_validate_run_create_missing_required_config():
    run_create = RunCreateStateless(
        agent_id="test-agent", input={"query": "test"}, config=None
    )

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.return_value = {
            "input": {"type": "object"},
            "output": {},
            "config": {"type": "object"},  # Config schema exists but config is None
        }

        with pytest.raises(
            InvalidFormatException, match='"config" is required for this agent'
        ):
            validate_run_create(run_create)


def test_validate_run_create_invalid_input():
    run_create = RunCreateStateless(
        agent_id="test-agent",
        input={"query": 123},  # Should be string
        config={"configurable": {"param": "value"}},
    )

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.return_value = {
            "input": {"type": "object", "properties": {"query": {"type": "string"}}},
            "output": {},
            "config": {"type": "object"},
        }

        with pytest.raises(InvalidFormatException):
            validate_run_create(run_create)


def test_validate_run_create_invalid_config():
    run_create = RunCreateStateless(
        agent_id="test-agent",
        input={"query": "test"},
        config={"configurable": {"param": 123}},  # Should be string
    )

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.return_value = {
            "input": {"type": "object"},
            "output": {},
            "config": {"type": "object", "properties": {"param": {"type": "string"}}},
        }

        with pytest.raises(InvalidFormatException):
            validate_run_create(run_create)


def test_validate_run_create_no_schema_requirements():
    run_create = RunCreateStateless(agent_id="test-agent", input=None, config=None)

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.return_value = {
            "input": None,  # No input schema requirement
            "output": {},
            "config": None,  # No config schema requirement
        }

        result = validate_run_create(run_create)
        assert result == run_create  # Should be valid


def test_validate_run_create_complex_schema():
    """Test validation with complex nested structures and array validations"""
    # Complex run with nested structures and arrays
    run_create = RunCreateStateful(
        agent_id="complex-agent",
        input={
            "search_query": "climate change",
            "filters": {
                "date_range": {"start": "2023-01-01", "end": "2023-12-31"},
                "sources": ["academic", "news"],
            },
            "result_limit": 10,
            "include_metadata": True,
            "tags": ["science", "environment", "research"],
        },
        config={
            "configurable": {
                "api_version": "v2",
                "search_depth": 3,
                "credentials": {"api_key": "test-key-123", "org_id": "org-456"},
                "search_preferences": [
                    {"field": "relevance", "weight": 0.7},
                    {"field": "recency", "weight": 0.3},
                ],
                "cache_ttl": 3600,
            }
        },
    )

    # Complex schema with nested objects, arrays, pattern properties and dependencies
    complex_input_schema = {
        "type": "object",
        "required": ["search_query"],
        "properties": {
            "search_query": {"type": "string", "minLength": 3},
            "filters": {
                "type": "object",
                "properties": {
                    "date_range": {
                        "type": "object",
                        "required": ["start", "end"],
                        "properties": {
                            "start": {"type": "string", "format": "date"},
                            "end": {"type": "string", "format": "date"},
                        },
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["academic", "news", "books", "web"],
                        },
                    },
                },
            },
            "result_limit": {"type": "integer", "minimum": 1, "maximum": 100},
            "include_metadata": {"type": "boolean"},
            "tags": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string"},
            },
        },
    }

    complex_config_schema = {
        "type": "object",
        "required": ["api_version", "search_depth"],
        "properties": {
            "api_version": {"type": "string", "pattern": "^v\\d+$"},
            "search_depth": {"type": "integer", "minimum": 1, "maximum": 5},
            "credentials": {
                "type": "object",
                "required": ["api_key"],
                "properties": {
                    "api_key": {"type": "string"},
                    "org_id": {"type": "string"},
                },
            },
            "search_preferences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["field", "weight"],
                    "properties": {
                        "field": {"type": "string"},
                        "weight": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                },
            },
            "cache_ttl": {"type": "integer"},
        },
    }

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.return_value = {
            "input": complex_input_schema,
            "output": {},
            "config": complex_config_schema,
        }

        # Should validate successfully
        result = validate_run_create(run_create)
        assert result == run_create


def test_validate_run_create_complex_schema_invalid():
    """Test validation failures with complex schemas"""
    # Invalid run with incorrect nested data types and constraint violations
    run_create = RunCreateStateful(
        agent_id="complex-agent",
        input={
            "search_query": "ai",  # too short (minLength: 3)
            "filters": {
                "date_range": {
                    "start": "2023-01-01",
                    "end": "not-a-date",  # invalid date format
                },
                "sources": ["academic", "invalid-source"],  # not in enum
            },
            "result_limit": 0,  # below minimum
            "tags": [],  # empty array (minItems: 1)
        },
        config={
            "configurable": {
                "api_version": "2.0",  # doesn't match pattern ^v\d+$
                "search_depth": 10,  # above maximum
                "search_preferences": [
                    {"field": "relevance", "weight": 1.5}  # weight above maximum
                ],
            }
        },
    )

    # Use same complex schemas as in the previous test
    complex_input_schema = {
        "type": "object",
        "required": ["search_query"],
        "properties": {
            "search_query": {"type": "string", "minLength": 3},
            "filters": {
                "type": "object",
                "properties": {
                    "date_range": {
                        "type": "object",
                        "required": ["start", "end"],
                        "properties": {
                            "start": {"type": "string", "format": "date"},
                            "end": {"type": "string", "format": "date"},
                        },
                    },
                    "sources": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["academic", "news", "books", "web"],
                        },
                    },
                },
            },
            "result_limit": {"type": "integer", "minimum": 1, "maximum": 100},
            "include_metadata": {"type": "boolean"},
            "tags": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string"},
            },
        },
    }

    complex_config_schema = {
        "type": "object",
        "required": ["api_version", "search_depth"],
        "properties": {
            "api_version": {"type": "string", "pattern": "^v\\d+$"},
            "search_depth": {"type": "integer", "minimum": 1, "maximum": 5},
            "credentials": {
                "type": "object",
                "required": ["api_key"],
                "properties": {
                    "api_key": {"type": "string"},
                    "org_id": {"type": "string"},
                },
            },
            "search_preferences": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["field", "weight"],
                    "properties": {
                        "field": {"type": "string"},
                        "weight": {"type": "number", "minimum": 0, "maximum": 1},
                    },
                },
            },
        },
    }

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.return_value = {
            "input": complex_input_schema,
            "output": {},
            "config": complex_config_schema,
        }

        # Should fail validation
        with pytest.raises(InvalidFormatException):
            validate_run_create(run_create)

def test_validate_run_create_complex_schema_additional_properties_fail():
    """Test validation with complex nested structures and array validations"""
    # Complex run with nested structures and arrays
    run_create = RunCreateStateful(
        agent_id="complex-agent",
        input={
            "echo_input": {
                "messages": [
                    {
                        "type": "human",
                        "content": "Hello I'm a developer"
                    }
                ]
            }
        },
        config={
            "configurable": {
                "to_upper": "false",
                "to_lower": "false"
                }
        },
    )
    complex_input_schema = {
        "$defs": {
            "Message": {
                "properties": {
                    "type": {
                        "$ref": "#/$defs/Type",
                        "description": "indicates the originator of the message, a human or an assistant"
                        },
                    "content": {
                        "description": "the content of the message",
                        "title": "Content",
                        "type": "string"
                        }
                },
                "required": [
                    "type",
                    "content"
                ],
                "title": "Message",
                "type": "object"
            },
            "Type": {
                "enum": [
                    "human",
                    "assistant",
                    "ai"
                ],
                "title": "Type",
                "type": "string"
            }
        },
        "properties": {
            "message": {
                "anyOf": [
                    {
                    "items": {
                        "$ref": "#/$defs/Message"
                    },
                    "type": "array"
                    },
                    {
                    "type": "null"
                    }
                ],
            "default": "null",
            "title": "Messages"
            }
        },
        "additionalProperties": False,
        "title": "InputState",
        "type": "object"
    }

    with mock.patch(
        "agent_workflow_server.services.validation.get_agent_schemas"
    ) as mock_get_schemas:
        mock_get_schemas.return_value = {
            "input": complex_input_schema,
            "output": {},
            "config": {},
        }

        # Should fail validation
        with pytest.raises(InvalidFormatException):
            validate_run_create(run_create)
