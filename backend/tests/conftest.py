"""Pytest configuration and shared fixtures for backend tests."""
from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> None:
    """Set up environment variables for testing.

    Ensures AI provider is configured with a test key so services can be instantiated.
    Story 9.0: Default switched from Baidu to DeepSeek.
    """
    # Set test AI provider configuration
    os.environ.setdefault("AI_PROVIDER", "deepseek")
    os.environ.setdefault("DEEPSEEK_API_KEY", "test-deepseek-api-key-for-testing")
    os.environ.setdefault("AI_MODEL", "deepseek-chat")
