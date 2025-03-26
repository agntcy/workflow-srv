# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Security
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

        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {"type": "apiKey", "in": "header", "name": API_KEY_NAME}
        }
        openapi_schema["security"] = [{"ApiKeyAuth": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
