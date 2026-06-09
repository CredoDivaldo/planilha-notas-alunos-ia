"""Chaos tests for Story 9.2 — Evolution API failure modes.

Verifies broadcast behaviour when the Evolution API is interrupted mid-broadcast.
These tests mock httpx to simulate docker kill scenarios deterministically, so
the suite is CI-friendly (no live Docker dependency). The same scenarios are
exercised live in docs/qa/chaos-test-9.2.md during operator validation.
"""
