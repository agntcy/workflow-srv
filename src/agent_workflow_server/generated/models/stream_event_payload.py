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
from typing import Any, List, Optional
from agent_workflow_server.generated.models.custom_run_result_update import CustomRunResultUpdate
from agent_workflow_server.generated.models.value_run_result_update import ValueRunResultUpdate
from typing import Union, Any, List, TYPE_CHECKING, Optional, Dict
from pydantic import StrictStr, Field
from pydantic import model_serializer
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

STREAMEVENTPAYLOAD_ONE_OF_SCHEMAS = ["CustomRunResultUpdate", "ValueRunResultUpdate"]

class StreamEventPayload(BaseModel):
    """
    A serialized JSON data structure carried in the SSE event data field. The event can carry either a full `ValueRunResultUpdate`, if streaming mode is `values` or an `CustomRunResultUpdate` if streaming mode is `custom`
    """
    # data type: ValueRunResultUpdate
    oneof_schema_1_validator: Optional[ValueRunResultUpdate] = None
    # data type: CustomRunResultUpdate
    oneof_schema_2_validator: Optional[CustomRunResultUpdate] = None
    actual_instance: Optional[Union[CustomRunResultUpdate, ValueRunResultUpdate]] = None
    one_of_schemas: List[str] = ["CustomRunResultUpdate", "ValueRunResultUpdate"]

    model_config = {
        "validate_assignment": True,
        "protected_namespaces": (),
    }


    discriminator_value_class_map: Dict[str, str] = {
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
    def actual_instance_must_validate_oneof(cls, v):
        instance = StreamEventPayload.model_construct()
        error_messages = []
        match = 0
        # validate data type: ValueRunResultUpdate
        if not isinstance(v, ValueRunResultUpdate):
            error_messages.append(f"Error! Input type `{type(v)}` is not `ValueRunResultUpdate`")
        else:
            match += 1
        # validate data type: CustomRunResultUpdate
        if not isinstance(v, CustomRunResultUpdate):
            error_messages.append(f"Error! Input type `{type(v)}` is not `CustomRunResultUpdate`")
        else:
            match += 1
        if match > 1:
            # more than 1 match
            raise ValueError("Multiple matches found when setting `actual_instance` in StreamEventPayload with oneOf schemas: CustomRunResultUpdate, ValueRunResultUpdate. Details: " + ", ".join(error_messages))
        elif match == 0:
            # no match
            raise ValueError("No match found when setting `actual_instance` in StreamEventPayload with oneOf schemas: CustomRunResultUpdate, ValueRunResultUpdate. Details: " + ", ".join(error_messages))
        else:
            return v

    @classmethod
    def from_dict(cls, obj: dict) -> Self:
        return cls.from_json(json.dumps(obj))

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Returns the object represented by the json string"""
        instance = cls.model_construct()
        error_messages = []
        match = 0

        # deserialize data into ValueRunResultUpdate
        try:
            instance.actual_instance = ValueRunResultUpdate.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))
        # deserialize data into CustomRunResultUpdate
        try:
            instance.actual_instance = CustomRunResultUpdate.from_json(json_str)
            match += 1
        except (ValidationError, ValueError) as e:
            error_messages.append(str(e))

        if match > 1:
            # more than 1 match
            raise ValueError("Multiple matches found when deserializing the JSON string into StreamEventPayload with oneOf schemas: CustomRunResultUpdate, ValueRunResultUpdate. Details: " + ", ".join(error_messages))
        elif match == 0:
            # no match
            raise ValueError("No match found when deserializing the JSON string into StreamEventPayload with oneOf schemas: CustomRunResultUpdate, ValueRunResultUpdate. Details: " + ", ".join(error_messages))
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
            return None

        to_dict = getattr(self.actual_instance, "to_dict", None)
        if callable(to_dict):
            return self.actual_instance.to_dict()
        else:
            # primitive type
            return self.actual_instance

    def to_str(self) -> str:
        """Returns the string representation of the actual instance"""
        return pprint.pformat(self.model_dump())


