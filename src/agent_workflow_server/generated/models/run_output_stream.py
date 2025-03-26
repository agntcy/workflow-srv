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
import pprint
import re  # noqa: F401
import json




from pydantic import BaseModel, ConfigDict, Field, StrictStr, field_validator
from typing import Any, ClassVar, Dict, List
from agent_workflow_server.generated.models.stream_event_payload import StreamEventPayload
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

class RunOutputStream(BaseModel):
    """
    Server-sent event containing one agent output event. Actual event type is carried inside the data.
    """ # noqa: E501
    id: StrictStr = Field(description="Unique identifier of the event")
    event: StrictStr = Field(description="Event type. This is the constant string `agent_event` to be compatible with SSE spec. The actual type differentiation is done in the event itself.")
    data: StreamEventPayload
    __properties: ClassVar[List[str]] = ["id", "event", "data"]

    @field_validator('event')
    def event_validate_enum(cls, value):
        """Validates the enum"""
        if value not in ('agent_event',):
            raise ValueError("must be one of enum values ('agent_event')")
        return value

    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
        "protected_namespaces": (),
    }


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of RunOutputStream from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        """
        _dict = self.model_dump(
            by_alias=True,
            exclude={
            },
            exclude_none=True,
        )
        # override the default output from pydantic by calling `to_dict()` of data
        if self.data:
            _dict['data'] = self.data.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: Dict) -> Self:
        """Create an instance of RunOutputStream from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "id": obj.get("id"),
            "event": obj.get("event"),
            "data": StreamEventPayload.from_dict(obj.get("data")) if obj.get("data") is not None else None
        })
        return _obj


