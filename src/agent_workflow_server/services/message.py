# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Literal, Optional

type MessageType = Literal["control", "message", "interrupt"]


class Message:
    def __init__(self, type: MessageType, data: Any, event: Optional[str] = None):
        self.type = type
        self.data = data
        self.event = event
