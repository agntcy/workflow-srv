# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

from pydantic import BaseModel

class TokenModel(BaseModel):
    """Defines a token model."""

    sub: str
