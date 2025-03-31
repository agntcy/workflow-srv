# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import atexit
import logging
import os
import pickle
from typing import Any, Dict

from dotenv import load_dotenv

import agent_workflow_server.logging.logger  # noqa: F401

from .models import Run, RunInfo
from .service import DBOperations

logger = logging.getLogger(__name__)

load_dotenv()


class InMemoryDB(DBOperations):
    """In-memory database with file persistence"""

    def __init__(self):
        self._runs: Dict[str, Run] = {}
        self._runs_info: Dict[str, RunInfo] = {}
        self._runs_output: Dict[str, Any] = {}

        use_fs_storage = os.getenv("AGWS_STORAGE_PERSIST", "True") == "True"
        if use_fs_storage:
            storage_file = os.getenv("AGWS_STORAGE_PATH") or "agws_storage.pkl"
            self.storage_file = storage_file
            self._load_from_file()
            # Register save on exit
            logger.debug("Registering database save handler on exit")
            atexit.register(self._save_to_file)

        super().__init__(self._runs, self._runs_info, self._runs_output)
        logger.debug("InMemoryDB initialization complete")

    def _save_to_file(self) -> None:
        """Save the current state to file"""
        try:
            logger.debug(
                "Runs: %d, Infos: %d, Outputs: %d",
                len(self._runs),
                len(self._runs_info),
                len(self._runs_output),
            )
            data = {
                "runs": self._runs,
                "runs_info": self._runs_info,
                "runs_output": self._runs_output,
            }
            with open(self.storage_file, "wb") as f:
                pickle.dump(data, f)
            logger.info("Database state saved successfully to %s", self.storage_file)
        except Exception as e:
            logger.error("Failed to save database state: %s", str(e))

    def _load_from_file(self) -> None:
        """Load the state from file if it exists"""
        if not os.path.exists(self.storage_file):
            logger.debug("No existing database file found at %s", self.storage_file)
            return

        try:
            logger.debug("Loading database state")
            with open(self.storage_file, "rb") as f:
                data = pickle.load(f)

            logger.debug(
                "Processing state: %d runs, %d runs_info records, %d runs_output",
                len(data.get("runs", {})),
                len(data.get("runs_info", {})),
                len(data.get("runs_output", {})),
            )

            self._runs = data.get("runs", {})
            self._runs_info = data.get("runs_info", {})
            self._runs_output = data.get("runs_output", {})
            logger.info(
                f"Database state loaded successfully from {os.path.abspath(self.storage_file)}"
            )

        except Exception as e:
            logger.error("Failed to load database state: %s", str(e))
            self._runs = {}
            self._runs_info = {}
            self._runs_output = {}


# Global instance of the database
logger.debug("Creating global InMemoryDB instance")
DB = InMemoryDB()
