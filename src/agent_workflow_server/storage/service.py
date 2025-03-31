# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import Run, RunInfo, RunStatus


class DBOperations:
    """CRUD operations for Runs"""

    def __init__(
        self,
        runs: Dict[str, Run],
        runs_info: Dict[str, RunInfo],
        runs_output: Dict[str, Any],
    ):
        self._runs: Dict[str, Run] = runs
        self._runs_info: Dict[str, RunInfo] = runs_info
        self._runs_output: Dict[str, Any] = runs_output

    def create_run(self, run: Run) -> Run:
        """Create a new Run"""
        run_id = str(run["run_id"])
        if run_id in self._runs:
            raise ValueError(f"Run with ID {run_id} already exists")
        self._runs[run_id] = run
        return run

    def get_run(self, run_id: str) -> Optional[Run]:
        """Get a Run by ID"""
        return self._runs.get(run_id)

    def list_runs(self) -> List[Run]:
        """List all Runs"""
        return list(self._runs.values())

    def update_run(self, run_id: str, updates: dict) -> Optional[Run]:
        """Update a Run with the given updates"""
        if run_id not in self._runs:
            return None
        run = self._runs[run_id]
        updated_run = {**run, **updates, "updated_at": datetime.now()}
        self._runs[run_id] = updated_run
        return updated_run

    def delete_run(self, run_id: str) -> bool:
        """Delete a Run and its associated info and output"""
        if run_id not in self._runs:
            return False
        del self._runs[run_id]
        if run_id in self._runs_info:
            del self._runs_info[run_id]
        if run_id in self._runs_output:
            del self._runs_output[run_id]
        return True

    def search_run(self, filters: dict) -> List[Run]:
        """Search Runs by filters"""
        results = []
        for run in self._runs.values():
            matches = True
            for key, value in filters.items():
                if key not in run or run[key] != value:
                    matches = False
                    break
            if matches:
                results.append(run)
        return results

    def get_run_status(self, run_id: str) -> Optional[RunStatus]:
        """Get the status of a Run"""
        run = self.get_run(run_id)
        return run.get("status") if run else None

    def update_run_status(self, run_id: str, status: RunStatus) -> Optional[Run]:
        """Update the status of a Run"""
        return self.update_run(run_id, {"status": status})

    def add_run_output(self, run_id: str, output: Any) -> None:
        """Add the output of a Run"""
        self._runs_output[run_id] = output

    def get_run_output(self, run_id: str) -> Optional[Any]:
        """Get the output of a Run"""
        return self._runs_output.get(run_id)

    def create_run_info(self, run_info: RunInfo) -> RunInfo:
        """Create a new Run info in the database"""
        run_id = str(run_info["run_id"])
        self._runs_info[run_id] = run_info
        return run_info

    def get_run_info(self, run_id: str) -> Optional[RunInfo]:
        """Get a Run info by run ID"""
        return self._runs_info.get(run_id)

    def list_run_info(self) -> List[RunInfo]:
        """List all Run info"""
        return list(self._runs_info.values())

    def delete_run_info(self, run_id: str) -> bool:
        """Delete a Run info by run ID"""

        if run_id not in self._runs_info:
            return False
        del self._runs_info[run_id]
        return True

    def update_run_info(self, run_id: str, updates: dict) -> Optional[RunInfo]:
        """Update a Run info"""
        if run_id not in self._runs_info:
            return None
        run_info = self._runs_info[run_id]
        updated_run_info = {**run_info, **updates}
        self._runs_info[run_id] = updated_run_info
        return updated_run_info
