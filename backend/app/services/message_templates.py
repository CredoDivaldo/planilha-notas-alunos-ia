"""WhatsApp message template rendering.

Substitutes placeholders in a professor-authored template with real values.
Supports both ``{{var}}`` (frontend default) and ``{var}`` syntaxes, plus
Portuguese names and English aliases.
"""
from __future__ import annotations

from typing import Any


def render_message_template(template: str | None, **variables: Any) -> str:
    """Render a message template.

    Recognised variables: nome/name, disciplina/subject, semestre,
    nota_final/nota/grade, resultado, numero/student_number.
    """
    if not template:
        template = (
            "Olá {{nome}}! A sua nota de {{disciplina}} é {{nota_final}}. "
            "Resultado: {{resultado}}. Cumprimentos."
        )
    nome = str(variables.get("nome", "") or "")
    disciplina = str(variables.get("disciplina", "") or "")
    semestre = str(variables.get("semestre", "") or "")
    nota = str(variables.get("nota", "") or "")
    resultado = str(variables.get("resultado", "") or "")
    numero = str(variables.get("numero", "") or "")

    mapping = {
        "nome": nome,
        "name": nome,
        "disciplina": disciplina,
        "subject": disciplina,
        "semestre": semestre,
        "nota_final": nota,
        "nota": nota,
        "grade": nota,
        "resultado": resultado,
        "numero": numero,
        "student_number": numero,
    }
    out = template
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", val).replace("{" + key + "}", val)
    return out
