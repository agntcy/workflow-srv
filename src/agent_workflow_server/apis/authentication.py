# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_401_UNAUTHORIZED

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "x-api-key"

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def authentication_with_api_key(
    api_key_header: str = Security(api_key_header),
) -> Optional[str]:
    # If no API key is configured, authentication is disabled
    if not API_KEY:
        return None

    # If API key is configured, validate the header
    if api_key_header == API_KEY:
        return api_key_header

    raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid API Key")


def setup_api_key_auth(app: FastAPI) -> None:
    """Setup API Key authentication for the FastAPI application"""

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )

        app.openapi_schema = add_authentication_to_spec(openapi_schema)
        return app.openapi_schema

    app.openapi = custom_openapi

    # Override the default swagger UI to include persistent auth
    def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_favicon_url="/static/favicon.png",
            init_oauth={},
            swagger_ui_parameters={
                "persistAuthorization": True,
                "displayRequestDuration": True,
                "tryItOutEnabled": True,
            },
        )

    app.swagger_ui_html = custom_swagger_ui_html


def add_authentication_to_spec(spec_dict: dict) -> dict:
    """Add API key authentication to an OpenAPI spec"""
    # Add security scheme
    if "components" not in spec_dict:
        spec_dict["components"] = {}

    spec_dict["components"]["securitySchemes"] = {
        "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": API_KEY_NAME}
    }

    # Add global security requirement
    spec_dict["security"] = [{"ApiKeyAuth": []}]

    # Ensure all operations have security requirement
    for path in spec_dict["paths"].values():
        for operation in path.values():
            if isinstance(operation, dict):
                operation["security"] = [{"ApiKeyAuth": []}]

    return spec_dict
