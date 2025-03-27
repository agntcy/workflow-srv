# Copyright AGNTCY Contributors (https://github.com/agntcy)
# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


@pytest.fixture(autouse=True)
def load_test_env():
    """Load test environment variables before each test"""
    # Store original environment
    original_env = dict(os.environ)

    # Load test environment
    env_path = Path(__file__).parent / ".env.test"
    load_dotenv(env_path, override=True)

    yield

    # Restore original environment instead of clearing everything
    os.environ.clear()
    os.environ.update(original_env)
