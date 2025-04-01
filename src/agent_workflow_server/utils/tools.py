# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def make_serializable(v: Any):
    if isinstance(v, list):
        return [make_serializable(vv) for vv in v]
    elif isinstance(v, dict):
        return {kk: make_serializable(vv) for kk, vv in v.items()}
    elif (
        isinstance(v, BaseModel) and hasattr(v, "model_dump") and callable(v.model_dump)
    ):
        return v.model_dump(mode="json")
    elif isinstance(v, BaseModel) and hasattr(v, "dict") and callable(v.dict):
        return v.dict()
    elif isinstance(v, Enum):
        return v.value
    else:
        return v
