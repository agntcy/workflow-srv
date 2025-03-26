# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Any


class Message:
    def __init__(self, topic: str, data: Any):
        self.topic = topic
        self.data = data
