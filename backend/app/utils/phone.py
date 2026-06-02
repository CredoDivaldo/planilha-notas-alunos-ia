"""Phone number normalization for WhatsApp integration.

Handles Evolution API remoteJid format normalization:
  - Input: "244912345678@s.whatsapp.net" or "+244912345678" or "00244912345678"
  - Output: "244912345678" (digits only, no @s.whatsapp.net, no +/00 prefix)

Supports Angola (+244), Portugal (+351), and generic formats.
"""
from __future__ import annotations


def normalize_phone(raw_phone: str) -> str:
    """Normalize a phone number for student lookup.

    Steps:
    1. Strip @s.whatsapp.net suffix (Evolution API format)
    2. Remove leading + or 00 (international prefix symbols)
    3. Keep digits only

    Args:
        raw_phone: Raw phone input (e.g., "244912345678@s.whatsapp.net", "+244912345678")

    Returns:
        Normalized phone string (digits only, e.g., "244912345678")

    Examples:
        >>> normalize_phone("244912345678@s.whatsapp.net")
        '244912345678'
        >>> normalize_phone("+244912345678")
        '244912345678'
        >>> normalize_phone("00244912345678")
        '244912345678'
        >>> normalize_phone("351912345678")
        '351912345678'
        >>> normalize_phone("+351 91 234 5678")
        '351912345678'
    """
    if not raw_phone:
        return ""

    # Step 1: Strip @s.whatsapp.net suffix
    phone = raw_phone.split("@")[0]

    # Step 2: Remove leading + or 00
    if phone.startswith("+"):
        phone = phone[1:]
    elif phone.startswith("00"):
        phone = phone[2:]

    # Step 3: Keep digits only
    phone = "".join(c for c in phone if c.isdigit())

    return phone
