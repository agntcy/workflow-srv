# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import logging
import os

from uvicorn.logging import ColourizedFormatter

handler = logging.StreamHandler()
colorformatter = ColourizedFormatter(
    fmt="%(levelprefix)s %(name)s %(message)s ", use_colors=True
)
handler.setFormatter(colorformatter)

CustomLoggerHandler = handler

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, handlers=[CustomLoggerHandler], force=True)
