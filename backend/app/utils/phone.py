"""Normalização de números de telefone (para o WhatsApp).

PT: O mesmo número pode chegar escrito de várias formas: "+244912345678",
"00244...", "244...@s.whatsapp.net" ou com espaços. Esta função reduz tudo a um
formato único — só dígitos — para depois conseguirmos comparar/encontrar o aluno.

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

    # Passo 1: tirar o sufixo "@s.whatsapp.net" (split("@")[0] = parte antes do @).
    phone = raw_phone.split("@")[0]

    # Passo 2: remover o prefixo internacional "+" ou "00" do início.
    if phone.startswith("+"):
        phone = phone[1:]
    elif phone.startswith("00"):
        phone = phone[2:]

    # Passo 3: ficar só com os dígitos (descarta espaços, traços, etc.).
    # "".join(...) junta numa string só os caracteres que são números.
    phone = "".join(c for c in phone if c.isdigit())

    return phone


def ensure_country_code(phone: str, default_code: str = "244") -> str:
    """Garante que o número tem o código de país (Angola = 244).

    Números angolanos têm 9 dígitos e começam por 9. Se o número já tiver
    o código de país (12 dígitos para Angola), devolve-o tal qual.

    Examples:
        >>> ensure_country_code("923557393")
        '244923557393'
        >>> ensure_country_code("244923557393")
        '244923557393'
        >>> ensure_country_code("+244923557393")
        '244923557393'
        >>> ensure_country_code("351912345678")
        '351912345678'
    """
    digits = normalize_phone(phone)
    if not digits:
        return ""
    if digits.startswith(default_code):
        return digits
    # 9 dígitos começando por 9 → número angolano local sem código de país
    if len(digits) == 9 and digits.startswith("9"):
        return default_code + digits
    return digits
