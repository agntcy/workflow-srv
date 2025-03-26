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




from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, StrictStr
from typing import Any, ClassVar, Dict, List, Optional
from agent_workflow_server.generated.models.run_create_stateless import RunCreateStateless
from agent_workflow_server.generated.models.run_status import RunStatus
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

class RunStateless(BaseModel):
    """
    Holds all the information of a stateless run
    """ # noqa: E501
    run_id: StrictStr = Field(description="The ID of the run.")
    thread_id: Optional[StrictStr] = Field(default=None, description="Optional Thread ID wher the Run belongs to. This is populated only for runs on agents agents supporting Threads.")
    agent_id: StrictStr = Field(description="The agent that was used for this run.")
    created_at: datetime = Field(description="The time the run was created.")
    updated_at: datetime = Field(description="The last time the run was updated.")
    status: RunStatus = Field(description="The status of the run. One of 'pending', 'error', 'success', 'timeout', 'interrupted'.")
    creation: RunCreateStateless
    __properties: ClassVar[List[str]] = ["run_id", "thread_id", "agent_id", "created_at", "updated_at", "status", "creation"]

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
        """Create an instance of RunStateless from a JSON string"""
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
        # override the default output from pydantic by calling `to_dict()` of creation
        if self.creation:
            _dict['creation'] = self.creation.to_dict()
        return _dict

    @classmethod
    def from_dict(cls, obj: Dict) -> Self:
        """Create an instance of RunStateless from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "run_id": obj.get("run_id"),
            "thread_id": obj.get("thread_id"),
            "agent_id": obj.get("agent_id"),
            "created_at": obj.get("created_at"),
            "updated_at": obj.get("updated_at"),
            "status": obj.get("status"),
            "creation": RunCreateStateless.from_dict(obj.get("creation")) if obj.get("creation") is not None else None
        })
        return _obj


