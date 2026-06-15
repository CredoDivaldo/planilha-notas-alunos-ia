"""Academic provisioning service — populate the normalized relational model.

The professor-facing flow is simple (create context, upload students CSV,
upload grades CSV, publish). These helpers translate that flow into the
normalized schema: ``professors`` / ``subjects`` / ``class_groups`` /
``teaching_assignments`` / ``assessment_definitions`` / ``students`` /
``class_enrollments`` / ``grade_entries``.

All functions:
- take an active SQLAlchemy ``Connection`` (the caller controls the
  transaction / commit), and
- are idempotent (safe to call repeatedly; they find-or-create).

This replaces the legacy CSV-shaped tables as the single source of truth.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import bindparam, text


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _slug(value: Any, maxlen: int = 60) -> str:
    """ASCII slug for stable, unique-ish codes (subjects, class groups)."""
    decomposed = unicodedata.normalize("NFD", str(value or ""))
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_only).strip("-").lower()
    return (slug or "item")[:maxlen]


# ---------------------------------------------------------------------------
# Teaching side: professor → subject/class_group → teaching_assignment → components
# ---------------------------------------------------------------------------


def ensure_professor(conn: Any, user_id: int, name: str | None) -> int:
    row = conn.execute(
        text("SELECT id FROM professors WHERE user_id = :uid LIMIT 1"),
        {"uid": user_id},
    ).fetchone()
    if row:
        return row[0]
    r = conn.execute(
        text(
            "INSERT INTO professors (user_id, full_name, created_at, updated_at)"
            " VALUES (:uid, :name, :now, :now) RETURNING id"
        ),
        {"uid": user_id, "name": (name or "Professor").strip(), "now": _now()},
    )
    return r.scalar_one()


def ensure_subject(conn: Any, name: str) -> int:
    code = _slug(name)
    row = conn.execute(
        text("SELECT id FROM subjects WHERE code = :code LIMIT 1"),
        {"code": code},
    ).fetchone()
    if row:
        return row[0]
    r = conn.execute(
        text(
            "INSERT INTO subjects (code, name, status, created_at, updated_at)"
            " VALUES (:code, :name, 'active', :now, :now) RETURNING id"
        ),
        {"code": code, "name": (name or code).strip(), "now": _now()},
    )
    return r.scalar_one()


def ensure_class_group(conn: Any, turma: str) -> int:
    code = _slug(turma)
    row = conn.execute(
        text("SELECT id FROM class_groups WHERE code = :code LIMIT 1"),
        {"code": code},
    ).fetchone()
    if row:
        return row[0]
    r = conn.execute(
        text(
            "INSERT INTO class_groups (code, name, status, created_at, updated_at)"
            " VALUES (:code, :name, 'active', :now, :now) RETURNING id"
        ),
        {"code": code, "name": (turma or code).strip(), "now": _now()},
    )
    return r.scalar_one()


def ensure_teaching_assignment(
    conn: Any,
    professor_id: int,
    subject_id: int,
    class_group_id: int,
    semester_id: int,
    shift_id: int,
) -> int:
    row = conn.execute(
        text(
            "SELECT id FROM teaching_assignments"
            " WHERE professor_id = :p AND subject_id = :su AND class_group_id = :c"
            "   AND semester_id = :se AND shift_id = :sh LIMIT 1"
        ),
        {"p": professor_id, "su": subject_id, "c": class_group_id, "se": semester_id, "sh": shift_id},
    ).fetchone()
    if row:
        return row[0]
    r = conn.execute(
        text(
            "INSERT INTO teaching_assignments"
            " (professor_id, class_group_id, subject_id, semester_id, shift_id, is_active,"
            "  created_at, updated_at)"
            " VALUES (:p, :c, :su, :se, :sh, :active, :now, :now) RETURNING id"
        ),
        {"p": professor_id, "c": class_group_id, "su": subject_id, "se": semester_id,
         "sh": shift_id, "active": True, "now": _now()},
    )
    return r.scalar_one()


def sync_components(conn: Any, teaching_assignment_id: int, components: list[dict]) -> list[int]:
    """Create/update ``assessment_definitions`` to match ``components``.

    Keyed by ``sort_order`` (the component's index). Returns the assessment
    definition ids in component order. Removes surplus components (and their
    grade entries) when the component count shrinks.
    """
    now = _now()
    existing = conn.execute(
        text(
            "SELECT id, sort_order FROM assessment_definitions"
            " WHERE teaching_assignment_id = :ta ORDER BY sort_order"
        ),
        {"ta": teaching_assignment_id},
    ).fetchall()
    existing_by_order = {int(r[1]): r[0] for r in existing}

    result_ids: list[int] = []
    for i, comp in enumerate(components):
        name = str(comp.get("name", "") or f"Componente {i + 1}")
        weight = comp.get("weight", 0)
        code = f"c{i}"
        if i in existing_by_order:
            ad_id = existing_by_order[i]
            conn.execute(
                text(
                    "UPDATE assessment_definitions"
                    " SET name = :n, weight = :w, code = :code, updated_at = :now WHERE id = :id"
                ),
                {"n": name, "w": weight, "code": code, "now": now, "id": ad_id},
            )
        else:
            r = conn.execute(
                text(
                    "INSERT INTO assessment_definitions"
                    " (teaching_assignment_id, code, name, weight, sort_order, created_at, updated_at)"
                    " VALUES (:ta, :code, :n, :w, :so, :now, :now) RETURNING id"
                ),
                {"ta": teaching_assignment_id, "code": code, "n": name, "w": weight, "so": i, "now": now},
            )
            ad_id = r.scalar_one()
        result_ids.append(ad_id)

    # Remove surplus components (and dependent grade entries) when count shrinks
    surplus = [ad_id for order, ad_id in existing_by_order.items() if order >= len(components)]
    if surplus:
        conn.execute(
            text("DELETE FROM grade_entries WHERE assessment_definition_id IN :ids").bindparams(
                bindparam("ids", expanding=True)
            ),
            {"ids": surplus},
        )
        conn.execute(
            text("DELETE FROM assessment_definitions WHERE id IN :ids").bindparams(
                bindparam("ids", expanding=True)
            ),
            {"ids": surplus},
        )
    return result_ids


def get_component_ids(conn: Any, teaching_assignment_id: int) -> list[int]:
    """Return assessment definition ids ordered by sort_order."""
    rows = conn.execute(
        text(
            "SELECT id FROM assessment_definitions"
            " WHERE teaching_assignment_id = :ta ORDER BY sort_order, id"
        ),
        {"ta": teaching_assignment_id},
    ).fetchall()
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# Student side: students → enrollments → grade entries
# ---------------------------------------------------------------------------


def ensure_student(
    conn: Any,
    student_number: str,
    name: str,
    phone: str | None = None,
    class_group_id: int | None = None,
) -> int:
    now = _now()
    row = conn.execute(
        text("SELECT id FROM students WHERE student_number = :sn LIMIT 1"),
        {"sn": student_number},
    ).fetchone()
    if row:
        conn.execute(
            text(
                "UPDATE students SET full_name = :n, phone = :p, updated_at = :now"
                " WHERE id = :id"
            ),
            {"n": name or "", "p": phone, "now": now, "id": row[0]},
        )
        return row[0]
    r = conn.execute(
        text(
            "INSERT INTO students"
            " (student_number, full_name, phone, current_class_group_id, created_at, updated_at)"
            " VALUES (:sn, :n, :p, :cg, :now, :now) RETURNING id"
        ),
        {"sn": student_number, "n": name or "", "p": phone, "cg": class_group_id, "now": now},
    )
    return r.scalar_one()


def enroll_student(conn: Any, academic_context_id: int, student_id: int) -> int:
    row = conn.execute(
        text(
            "SELECT id FROM class_enrollments"
            " WHERE academic_context_id = :c AND student_id = :s LIMIT 1"
        ),
        {"c": academic_context_id, "s": student_id},
    ).fetchone()
    if row:
        return row[0]
    r = conn.execute(
        text(
            "INSERT INTO class_enrollments"
            " (academic_context_id, student_id, enrollment_status, created_at, updated_at)"
            " VALUES (:c, :s, 'active', :now, :now) RETURNING id"
        ),
        {"c": academic_context_id, "s": student_id, "now": _now()},
    )
    return r.scalar_one()


def upsert_grade(
    conn: Any,
    student_id: int,
    teaching_assignment_id: int,
    assessment_definition_id: int,
    value: Any,
    user_id: int | None = None,
) -> int:
    """Insert/update a grade entry (status=validated). Keyed by (student, assessment)."""
    now = _now()
    row = conn.execute(
        text(
            "SELECT id FROM grade_entries"
            " WHERE student_id = :s AND assessment_definition_id = :a LIMIT 1"
        ),
        {"s": student_id, "a": assessment_definition_id},
    ).fetchone()
    if row:
        conn.execute(
            text(
                "UPDATE grade_entries SET raw_value = :v, normalized_value = :v,"
                " status = 'validated', updated_by_user_id = :u, updated_at = :now WHERE id = :id"
            ),
            {"v": value, "u": user_id, "now": now, "id": row[0]},
        )
        return row[0]
    r = conn.execute(
        text(
            "INSERT INTO grade_entries"
            " (student_id, teaching_assignment_id, assessment_definition_id, raw_value,"
            "  normalized_value, status, updated_by_user_id, created_at, updated_at)"
            " VALUES (:s, :ta, :a, :v, :v, 'validated', :u, :now, :now) RETURNING id"
        ),
        {"s": student_id, "ta": teaching_assignment_id, "a": assessment_definition_id,
         "v": value, "u": user_id, "now": now},
    )
    return r.scalar_one()
