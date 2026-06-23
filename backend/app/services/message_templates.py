"""Preenchimento de modelos de mensagem do WhatsApp.

PT: O professor escreve um modelo com "espaços reservados" (ex.: "Olá {{nome}}, a
tua nota é {{nota_final}}"). Esta função substitui cada espaço pelo valor real do
aluno, gerando a mensagem final personalizada. Aceita {{var}} e {var}, e nomes em
português ou inglês para a mesma variável.
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

    # Dicionário que liga cada nome de variável ao valor a inserir.
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
    # Para cada variável, substitui no texto tanto {{var}} como {var} pelo valor.
    out = template
    for key, val in mapping.items():
        out = out.replace("{{" + key + "}}", val).replace("{" + key + "}", val)
    return out
