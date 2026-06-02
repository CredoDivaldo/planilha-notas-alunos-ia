"""Pytest configuration and shared fixtures for backend tests."""
from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """Set up environment variables for testing.

    Ensures AI provider is configured with a test key so services can be instantiated.
    """
    # Set test AI provider configuration
    os.environ.setdefault("AI_PROVIDER", "baidu")
    os.environ.setdefault("BAIDU_API_KEY", "test-baidu-api-key-for-testing")
    os.environ.setdefault("AI_MODEL", "ernie-3.5-8k")
