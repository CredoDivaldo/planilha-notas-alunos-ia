"""Shared helpers for the legacy CSV grade path.

Both the broadcast (``professor.py``) and the chatbot (``ai_chatbot.py``)
need to take the per-component rows stored in ``legacy_grades`` and turn
them into a single weighted final grade, using the component weights kept
in ``academic_contexts.components_json``. They also share the message
template rendering (supporting both ``{{var}}`` and ``{var}`` syntaxes).

Keeping this logic in one place guarantees the WhatsApp broadcast and the
chatbot always compute the same final grade.
"""
from __future__ import annotations

from typing import Any


def map_legacy_grades_to_components(
    grade_rows: list[tuple[Any, Any]],
    components: list[dict[str, Any]],
) -> dict[str, float]:
    """Map ``(subject, value)`` legacy rows onto component indices.

    ``subject`` stores the component id ("0", "1", ...) for imports done
    via the grades modal, or the component name, or nothing (old imports).
    Returns a dict ``{component_index_str: float_value}``.
    """
    result: dict[str, float] = {}
    unmatched: list[float] = []
    for subject, value in grade_rows:
        try:
            v = float(value)
        except (TypeError, ValueError):
            continue
        matched: str | None = None
        if subject is not None:
            subj = str(subject)
            # Direct index match ("0", "1", ...)
            for i in range(len(components)):
                if subj == str(i):
                    matched = str(i)
                    break
            # Name match
            if matched is None:
                for i, c in enumerate(components):
                    name = str(c.get("name", ""))
                    if name and subj.lower() == name.lower():
                        matched = str(i)
                        break
        if matched is not None:
            result[matched] = v
        else:
            unmatched.append(v)
    # Position fallback for rows that didn't match (old untagged imports)
    empty = [str(i) for i in range(len(components)) if str(i) not in result]
    for j, v in enumerate(unmatched):
        if j < len(empty):
            result[empty[j]] = v
    return result


def compute_final_grade(
    component_values: dict[str, float],
    components: list[dict[str, Any]],
) -> float | None:
    """Compute the weighted final grade. Mirrors frontend ``calcNotaFinal``.

    Returns ``None`` when any component is missing (incomplete) or when
    there are no components defined.
    """
    if not components:
        return None
    total = 0.0
    for i, c in enumerate(components):
        v = component_values.get(str(i))
        if v is None:
            return None
        try:
            weight = float(c.get("weight", 0))
        except (TypeError, ValueError):
            weight = 0.0
        total += v * weight / 100
    return round(total * 10) / 10


def render_message_template(template: str | None, **variables: Any) -> str:
    """Render a message template, supporting both ``{{var}}`` and ``{var}``.

    Recognised variables (Portuguese + English aliases):
    nome/name, disciplina/subject, semestre, nota_final/nota/grade,
    resultado, numero/student_number.
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
