"""Unit tests for phone number normalization utility.

Tests phone format handling for Angola (+244), Portugal (+351), and generic formats.
"""
from __future__ import annotations

import pytest

from backend.app.utils.phone import normalize_phone


class TestPhoneNormalization:
    """Test phone normalization function."""

    def test_normalize_whatsapp_format_angola(self) -> None:
        """Normalize Evolution API remoteJid format (Angola)."""
        result = normalize_phone("244912345678@s.whatsapp.net")
        assert result == "244912345678"

    def test_normalize_whatsapp_format_portugal(self) -> None:
        """Normalize Evolution API remoteJid format (Portugal)."""
        result = normalize_phone("351912345678@s.whatsapp.net")
        assert result == "351912345678"

    def test_normalize_plus_prefix_angola(self) -> None:
        """Normalize +244 format."""
        result = normalize_phone("+244912345678")
        assert result == "244912345678"

    def test_normalize_plus_prefix_portugal(self) -> None:
        """Normalize +351 format."""
        result = normalize_phone("+351912345678")
        assert result == "351912345678"

    def test_normalize_double_zero_prefix_angola(self) -> None:
        """Normalize 00244 format."""
        result = normalize_phone("00244912345678")
        assert result == "244912345678"

    def test_normalize_double_zero_prefix_portugal(self) -> None:
        """Normalize 00351 format."""
        result = normalize_phone("00351912345678")
        assert result == "351912345678"

    def test_normalize_with_spaces_portugal(self) -> None:
        """Normalize with spaces (+351 91 234 5678)."""
        result = normalize_phone("+351 91 234 5678")
        assert result == "351912345678"

    def test_normalize_with_hyphens_angola(self) -> None:
        """Normalize with hyphens (+244-91-234-5678)."""
        result = normalize_phone("+244-91-234-5678")
        assert result == "244912345678"

    def test_normalize_plain_digits_angola(self) -> None:
        """Normalize plain digit format without any prefix."""
        result = normalize_phone("244912345678")
        assert result == "244912345678"

    def test_normalize_plain_digits_portugal(self) -> None:
        """Normalize plain digit format without any prefix."""
        result = normalize_phone("351912345678")
        assert result == "351912345678"

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        result = normalize_phone("")
        assert result == ""

    def test_none_like_string(self) -> None:
        """String with only non-digit chars returns empty."""
        result = normalize_phone("@s.whatsapp.net")
        assert result == ""

    def test_complex_mixed_format(self) -> None:
        """Complex format with multiple prefixes and separators."""
        result = normalize_phone("+244-91-234-5678@s.whatsapp.net")
        assert result == "244912345678"

    def test_parentheses_format(self) -> None:
        """Format with parentheses (common in some regions)."""
        result = normalize_phone("+244 (91) 234-5678")
        assert result == "244912345678"

    def test_short_number(self) -> None:
        """Short number without country code."""
        result = normalize_phone("912345678")
        assert result == "912345678"

    def test_with_dots_separators(self) -> None:
        """Format with dots as separators."""
        result = normalize_phone("+244.91.234.5678")
        assert result == "244912345678"
