# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os

import pytest
from fastapi import FastAPI, HTTPException
from pytest_mock import MockerFixture

from agent_workflow_server.apis.authentication import (
    API_KEY_NAME,
    authentication_with_api_key,
    setup_api_key_auth,
)


@pytest.mark.asyncio
async def test_authentication_with_api_key_disabled(mocker: MockerFixture):
    # Test when API_KEY is not set (authentication disabled)
    mocker.patch.dict(os.environ, {}, clear=True)
    mocker.patch("agent_workflow_server.apis.authentication.API_KEY", None)

    result = await authentication_with_api_key("any-key")
    assert result is None


@pytest.mark.asyncio
async def test_authentication_with_api_key_valid(mocker: MockerFixture):
    # Test when API_KEY is set and the header matches
    test_api_key = "test-api-key"
    mocker.patch.dict(os.environ, {"API_KEY": test_api_key})
    mocker.patch("agent_workflow_server.apis.authentication.API_KEY", test_api_key)

    result = await authentication_with_api_key(test_api_key)
    assert result == test_api_key


@pytest.mark.asyncio
async def test_authentication_with_api_key_invalid(mocker: MockerFixture):
    # Test when API_KEY is set but the header doesn't match
    test_api_key = "test-api-key"
    mocker.patch.dict(os.environ, {"API_KEY": test_api_key})
    mocker.patch("agent_workflow_server.apis.authentication.API_KEY", test_api_key)

    with pytest.raises(HTTPException) as excinfo:
        await authentication_with_api_key("wrong-api-key")

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid API Key"


@pytest.mark.asyncio
async def test_authentication_with_api_key_missing(mocker: MockerFixture):
    # Test when API_KEY is set but no header is provided
    test_api_key = "test-api-key"
    mocker.patch.dict(os.environ, {"API_KEY": test_api_key})
    mocker.patch("agent_workflow_server.apis.authentication.API_KEY", test_api_key)

    with pytest.raises(HTTPException) as excinfo:
        await authentication_with_api_key(None)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Invalid API Key"


def test_setup_api_key_auth_initializes_openapi_schema():
    # Create a FastAPI app with no schema yet
    app = FastAPI()
    assert app.openapi_schema is None

    # Setup API key auth
    setup_api_key_auth(app)

    # Call the custom openapi function (which should now be set)
    schema = app.openapi()

    # Verify schema was created
    assert app.openapi_schema is not None
    assert schema is app.openapi_schema


def test_setup_api_key_auth_adds_security_components():
    app = FastAPI()
    setup_api_key_auth(app)
    schema = app.openapi()

    # Verify security components were added
    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "ApiKeyAuth" in schema["components"]["securitySchemes"]

    auth_scheme = schema["components"]["securitySchemes"]["ApiKeyAuth"]
    assert auth_scheme["type"] == "apiKey"
    assert auth_scheme["in"] == "header"
    assert auth_scheme["name"] == API_KEY_NAME


def test_setup_api_key_auth_adds_global_security():
    app = FastAPI()
    setup_api_key_auth(app)
    schema = app.openapi()

    # Verify global security was added
    assert "security" in schema
    assert [{"ApiKeyAuth": []}] == schema["security"]


def test_setup_api_key_auth_adds_security_to_operations():
    # Create a FastAPI app with a route
    app = FastAPI()

    @app.get("/test")
    def test_route():
        return {"message": "test"}

    setup_api_key_auth(app)
    schema = app.openapi()

    # Verify security was added to the operation
    test_path = schema["paths"]["/test"]
    assert "get" in test_path
    assert "security" in test_path["get"]
    assert [{"ApiKeyAuth": []}] == test_path["get"]["security"]


def test_setup_api_key_auth_preserves_existing_schema():
    app = FastAPI()

    # Set an existing schema
    existing_schema = {"test": "value"}
    app.openapi_schema = existing_schema

    setup_api_key_auth(app)
    schema = app.openapi()

    # Verify the existing schema was preserved
    assert schema is existing_schema
