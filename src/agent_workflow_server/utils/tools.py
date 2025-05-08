# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import importlib
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


def load_from_module(module: str, obj: str) -> object:
    """
    Dynamically loads a class, variable, or object from a given module.

    Args:
        module (str): The module path where the import resides (e.g., 'myapp.mymodule').
        obj (str): The name of the object to import from the module (e.g., 'MyObject').

    Returns:
        object: The imported class, variable, or object.

    Raises:
        ModuleNotFoundError: If the module cannot be found.
        AttributeError: If the obj is not found in the module.
    """
    try:
        # Dynamically import the module
        imported_module = importlib.import_module(module)

        # Retrieve the specified object from the module
        return getattr(imported_module, obj)
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(f"Module '{module}' could not be found.") from e
    except AttributeError as e:
        raise AttributeError(
            f"'{obj}' could not be found in the module '{module}'."
        ) from e
