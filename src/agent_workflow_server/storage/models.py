# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict

RunStatus = Literal["pending", "error", "success", "timeout", "interrupted"]


class Interrupt(TypedDict):
    """Definition for an Interrupt message"""

    event: str
    ai_data: Any
    user_data: Optional[Any]


class Config(TypedDict):
    tags: Optional[List[str]]
    recursion_limit: Optional[int]
    configurable: Optional[Dict[str, Any]]


class Run(TypedDict):
    """Definition for a Run record"""

    run_id: str
    agent_id: str
    thread_id: str
    input: Optional[Dict[str, Any]]
    config: Optional[Config]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    status: RunStatus
    interrupt: Optional[Interrupt]  # last interrupt (if any)


class RunInfo(TypedDict):
    """Definition of statistics information about a Run"""

    run_id: str
    queued_at: datetime
    attempts: Optional[int]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    exec_s: Optional[float]
    queue_s: Optional[float]
