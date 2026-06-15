"""Authentication router — login, register, change-password.

Session IDs are returned as `access_token` so the frontend can use
`Authorization: Bearer <session_id>` on every request.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.auth.password import hash_password, verify_password
from backend.app.auth.sessions import create_session
from backend.app.config import get_settings
from backend.app.database import build_engine

LOGGER = logging.getLogger("backend.app.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


# ── DB helper ─────────────────────────────────────────────────────────────────

def _get_db(request: Request):
    """Yield a SQLAlchemy connection from the app-level engine."""
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        settings = get_settings()
        engine = build_engine(settings.database_url)
    with engine.connect() as conn:
        yield conn


DbConn = Annotated[object, Depends(_get_db)]


# ── Schemas ───────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email_or_student_number: str
    password: str
    role: str = "professor"


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Endereço de email inválido.")
        return v
    institution: str = "Universidade Lusíada de Angola"
    faculty: str = ""
    disciplines: list[str] = []

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A palavra-passe deve ter pelo menos 8 caracteres.")
        if not any(c.isupper() for c in v):
            raise ValueError("A palavra-passe deve conter pelo menos uma letra maiúscula.")
        return v


class ChangePasswordRequest(BaseModel):
    new_password: str
    confirm_password: str


class AuthResponse(BaseModel):
    id: str
    name: str
    role: str
    access_token: str
    requires_password_change: bool = False


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, request: Request, conn: DbConn):
    identifier = body.email_or_student_number.strip().lower()

    row = conn.execute(
        text(
            "SELECT id, username, password_hash, role, display_name,"
            " must_change_password, is_active"
            " FROM users WHERE username = :username LIMIT 1"
        ),
        {"username": identifier},
    ).fetchone()

    if not row or not verify_password(row.password_hash, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login failed.")

    if not row.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta suspensa.")

    conn.execute(
        text("UPDATE users SET last_login_at = :now WHERE id = :uid"),
        {"now": datetime.now(UTC).replace(tzinfo=None), "uid": row.id},
    )

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    session_id = create_session(conn, user_id=row.id, ip_address=ip, user_agent=ua)
    conn.commit()

    display = row.display_name or row.username
    return AuthResponse(
        id=str(row.id),
        name=display,
        role=row.role,
        access_token=session_id,
        requires_password_change=bool(row.must_change_password),
    )


# ── Register ──────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=AuthResponse)
async def register(body: RegisterRequest, request: Request, conn: DbConn):
    username = body.email.lower().strip()

    existing = conn.execute(
        text("SELECT id FROM users WHERE username = :u LIMIT 1"),
        {"u": username},
    ).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com este email.",
        )

    pw_hash = hash_password(body.password)
    disciplines_json = json.dumps(body.disciplines, ensure_ascii=False) if body.disciplines else None
    now = datetime.now(UTC).replace(tzinfo=None)

    result = conn.execute(
        text(
            "INSERT INTO users"
            " (username, password_hash, role, display_name, institution, faculty, disciplines,"
            "  must_change_password, is_active, created_at, updated_at)"
            " VALUES"
            " (:username, :pw_hash, 'professor', :display_name, :institution, :faculty,"
            "  :disciplines, false, true, :now, :now)"
            " RETURNING id"
        ),
        {
            "username": username,
            "pw_hash": pw_hash,
            "display_name": body.full_name.strip(),
            "institution": body.institution.strip(),
            "faculty": body.faculty.strip() or None,
            "disciplines": disciplines_json,
            "now": now,
        },
    )
    user_id = result.scalar_one()

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    session_id = create_session(conn, user_id=user_id, ip_address=ip, user_agent=ua)
    conn.commit()

    LOGGER.info("professor_registered", extra={"user_id": user_id, "username": username})
    return AuthResponse(
        id=str(user_id),
        name=body.full_name.strip(),
        role="professor",
        access_token=session_id,
        requires_password_change=False,
    )


# ── Change password ───────────────────────────────────────────────────────────

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(body: ChangePasswordRequest, request: Request, conn: DbConn):
    if body.new_password != body.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="As palavras-passe não coincidem.",
        )
    if len(body.new_password) < 8 or not any(c.isupper() for c in body.new_password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A palavra-passe não cumpre os requisitos mínimos.",
        )

    # Resolve session from Bearer token
    auth_header = request.headers.get("authorization", "")
    session_id = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else None
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida.")

    now = datetime.now(UTC).replace(tzinfo=None)
    session_row = conn.execute(
        text(
            "SELECT user_id FROM user_sessions"
            " WHERE id = :sid AND is_active = true AND expires_at > :now LIMIT 1"
        ),
        {"sid": session_id, "now": now},
    ).fetchone()
    if not session_row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada.")

    new_hash = hash_password(body.new_password)
    conn.execute(
        text(
            "UPDATE users SET password_hash = :ph, must_change_password = false,"
            " updated_at = :now WHERE id = :uid"
        ),
        {"ph": new_hash, "now": now, "uid": session_row.user_id},
    )
    conn.commit()
