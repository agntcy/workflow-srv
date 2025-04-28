# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict, Optional, TypedDict


class ThreadState(TypedDict):
    """Definition of a ThreadState record"""

    checkpoint_id: str
    values: Dict[str, Any]
    metadata: Optional[Dict[str, Any]]
