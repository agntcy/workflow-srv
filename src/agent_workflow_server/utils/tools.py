# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import uuid
from enum import Enum

from pydantic import BaseModel


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def serialize_to_dict(v):
    if isinstance(v, list):
        return [serialize_to_dict(vv) for vv in v]
    elif isinstance(v, dict):
        return {kk: serialize_to_dict(vv) for kk, vv in v.items()}
    elif isinstance(v, BaseModel):
        return v.model_dump()
    elif isinstance(v, Enum):
        return v.value
    else:
        return v
