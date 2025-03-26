# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

# coding: utf-8

"""
    Agent Connect Protocol

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)

    The version of the OpenAPI document: 0.2.1
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
from inspect import getfullargspec
import json
import pprint
import re  # noqa: F401



from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError, field_validator
from typing import List, Optional
from agent_workflow_server.generated.models.streaming_mode import StreamingMode
from typing import Union, Any, List, TYPE_CHECKING, Optional, Dict
from pydantic import StrictStr, Field
from pydantic import model_serializer

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

STREAMMODE_ANY_OF_SCHEMAS = ["List[StreamingMode]", "StreamingMode"]

class StreamMode(BaseModel):
    """
    If populated, indicates that the client requests to stream results with the specified streaming mode(s). The requested streaming mode(s) must be one or more of those supported by the agent as declared in agent ACP descriptor  under `specs.capabilities`
    """

    # data type: List[StreamingMode]
    anyof_schema_1_validator: Optional[List[StreamingMode]] = None
    # data type: StreamingMode
    anyof_schema_2_validator: Optional[StreamingMode] = None
    if TYPE_CHECKING:
        actual_instance: Optional[Union[List[StreamingMode], StreamingMode]] = None
    else:
        actual_instance: Any = None
    any_of_schemas: List[str] = [STREAMMODE_ANY_OF_SCHEMAS]

    model_config = {
        "validate_assignment": True,
        "protected_namespaces": (),
    }

    def __init__(self, *args, **kwargs) -> None:
        if args:
            if len(args) > 1:
                raise ValueError("If a position argument is used, only 1 is allowed to set `actual_instance`")
            if kwargs:
                raise ValueError("If a position argument is used, keyword arguments cannot be used.")
            super().__init__(actual_instance=args[0])
        else:
            super().__init__(actual_instance={**kwargs})

    @field_validator('actual_instance')
    def actual_instance_must_validate_anyof(cls, v):
        if v is None:
            return v

        instance = StreamMode.model_construct()
        error_messages = []
        # validate data type: List[StreamingMode]
        try:
            instance.anyof_schema_1_validator = v
            return v
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # validate data type: StreamingMode
        if not isinstance(v, StreamingMode):
            error_messages.append(f"Error! Input type `{type(v)}` is not `StreamingMode`")
        else:
            return v

        if error_messages:
            # no match
            raise ValueError("No match found when setting the actual_instance in StreamMode with anyOf schemas: List[StreamingMode], StreamingMode. Details: " + ", ".join(error_messages))
        else:
            return v

    @classmethod
    def from_dict(cls, obj: dict) -> Self:
        return cls.from_json(json.dumps(obj))

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Returns the object represented by the json string"""
        instance = cls.model_construct()
        if json_str is None:
            return instance

        error_messages = []
        # deserialize data into List[StreamingMode]
        try:
            # validation
            instance.anyof_schema_1_validator = json.loads(json_str)
            # assign value to actual_instance
            instance.actual_instance = instance.anyof_schema_1_validator
            return instance
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # anyof_schema_2_validator: Optional[StreamingMode] = None
        try:
            instance.actual_instance = StreamingMode.from_json(json_str)
            return instance
        except (ValidationError, ValueError) as e:
             error_messages.append(str(e))

        if error_messages:
            # no match
            raise ValueError("No match found when deserializing the JSON string into StreamMode with anyOf schemas: List[StreamingMode], StreamingMode. Details: " + ", ".join(error_messages))
        else:
            return instance

    def to_json(self) -> str:
        """Returns the JSON representation of the actual instance"""
        if self.actual_instance is None:
            return "null"

        to_json = getattr(self.actual_instance, "to_json", None)
        if callable(to_json):
            return self.actual_instance.to_json()
        else:
            return json.dumps(self.actual_instance)
    
    @model_serializer()
    def to_dict(self) -> Dict:
        """Returns the dict representation of the actual instance"""
        if self.actual_instance is None:
            return "null"

        to_json = getattr(self.actual_instance, "to_json", None)
        if callable(to_json):
            return self.actual_instance.to_dict()
        else:
            # primitive type
            return self.actual_instance

    def to_str(self) -> str:
        """Returns the string representation of the actual instance"""
        return pprint.pformat(self.model_dump())


