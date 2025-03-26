# coding: utf-8

"""
    Agent Connect Protocol

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 0.2.1
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import json
import pprint
import re  # noqa: F401
from enum import Enum



try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class RunStatus(str, Enum):
    """
    RunStatus
    """

    """
    allowed enum values
    """
    PENDING = 'pending'
    ERROR = 'error'
    SUCCESS = 'success'
    TIMEOUT = 'timeout'
    INTERRUPTED = 'interrupted'

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of RunStatus from a JSON string"""
        return cls(json.loads(json_str))


