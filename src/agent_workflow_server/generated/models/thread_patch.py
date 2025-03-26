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




from pydantic import BaseModel, ConfigDict, Field
from typing import Any, ClassVar, Dict, List, Optional
from agent_workflow_server.generated.models.message import Message
from agent_workflow_server.generated.models.thread_checkpoint import ThreadCheckpoint
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

class ThreadPatch(BaseModel):
    """
    Payload for updating a thread.
    """ # noqa: E501
    checkpoint: Optional[ThreadCheckpoint] = Field(default=None, description="The identifier of the checkpoint to branch from. Ignored for metadata-only patches. If not provided, defaults to the latest checkpoint.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata to merge with existing thread metadata.")
    values: Optional[Dict[str, Any]] = Field(default=None, description="The thread state. The schema is described in agent ACP descriptor under 'spec.thread_state'.")
    messages: Optional[List[Message]] = Field(default=None, description="The current Messages of the thread. If messages are contained in Thread.values, implementations should remove them from values when returning messages. When this key isn't present it means the thread/agent doesn't support messages.")
    __properties: ClassVar[List[str]] = ["checkpoint", "metadata", "values", "messages"]

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
        """Create an instance of ThreadPatch from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of checkpoint
        if self.checkpoint:
            _dict['checkpoint'] = self.checkpoint.to_dict()
        # override the default output from pydantic by calling `to_dict()` of each item in messages (list)
        _items = []
        if self.messages:
            for _item in self.messages:
                if _item:
                    _items.append(_item.to_dict())
            _dict['messages'] = _items
        return _dict

    @classmethod
    def from_dict(cls, obj: Dict) -> Self:
        """Create an instance of ThreadPatch from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "checkpoint": ThreadCheckpoint.from_dict(obj.get("checkpoint")) if obj.get("checkpoint") is not None else None,
            "metadata": obj.get("metadata"),
            "values": obj.get("values"),
            "messages": [Message.from_dict(_item) for _item in obj.get("messages")] if obj.get("messages") is not None else None
        })
        return _obj


