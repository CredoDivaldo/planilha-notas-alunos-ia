"""Router de AUTENTICAÇÃO — login, registo e troca de palavra-passe.

PT: Reúne os endpoints que tratam de "quem é o utilizador":
  POST /auth/login            → entrar (devolve um token de sessão)
  POST /auth/register         → criar conta de professor
  POST /auth/change-password  → trocar a senha
  POST /auth/student/...      → primeiro acesso do aluno
  GET  /auth/me               → dados do utilizador autenticado
No fim do login devolvemos o id da sessão como `access_token`; o frontend passa-o
depois em cada pedido no cabeçalho `Authorization: Bearer <token>`.
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

# "Dependência" do FastAPI: fornece uma ligação à BD a cada endpoint que a peça.
# Usa `yield` (gerador): entrega a ligação e, no fim do pedido, fecha-a sozinha.
def _get_db(request: Request):
    """Fornece (yield) uma ligação SQLAlchemy a partir do engine da app."""
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        settings = get_settings()
        engine = build_engine(settings.database_url)
    with engine.connect() as conn:
        yield conn


# Atalho de tipo: escrever `conn: DbConn` num endpoint = "injecta aqui o _get_db".
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

    # @field_validator: o Pydantic corre esta função para validar o campo "email"
    # automaticamente quando os dados chegam. Se levantar ValueError, devolve erro 422.
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

    # Valida a força da senha: mínimo 8 caracteres e pelo menos uma maiúscula.
    # `any(c.isupper() for c in v)` → True se ALGUM caractere for maiúsculo.
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


class StudentStatusRequest(BaseModel):
    student_number: str


class StudentStatusResponse(BaseModel):
    found_in_roster: bool
    has_account: bool


class StudentActivateRequest(BaseModel):
    student_number: str
    password: str
    confirm_password: str


class AuthResponse(BaseModel):
    id: str
    name: str
    role: str
    access_token: str
    requires_password_change: bool = False


class MeResponse(BaseModel):
    id: str
    name: str
    role: str
    disciplines: list[str] = []
    contexts_count: int = 0


# ── Login ─────────────────────────────────────────────────────────────────────

# POST /auth/login → valida credenciais e devolve um token de sessão.
# `body` chega validado pelo schema; `conn` é injectada pela dependência _get_db.
@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, request: Request, conn: DbConn):
    identifier = body.email_or_student_number.strip().lower()

    # Procura o utilizador pelo nome de utilizador (email ou nº de aluno).
    row = conn.execute(
        text(
            "SELECT id, username, password_hash, role, display_name,"
            " must_change_password, is_active"
            " FROM users WHERE username = :username LIMIT 1"
        ),
        {"username": identifier},
    ).fetchone()

    # Falha se o utilizador não existe OU se a senha não bate certo com o hash.
    # (Mesma mensagem nos dois casos para não revelar qual deles falhou.)
    if not row or not verify_password(row.password_hash, body.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login failed.")

    if not row.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta suspensa.")

    conn.execute(
        text("UPDATE users SET last_login_at = :now WHERE id = :uid"),
        {"now": datetime.now(UTC).replace(tzinfo=None), "uid": row.id},
    )

    # Credenciais válidas → cria sessão e devolve o seu id como access_token.
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    session_id = create_session(conn, user_id=row.id, ip_address=ip, user_agent=ua)
    conn.commit()

    display = row.display_name or row.username  # usa o nome; se vazio, o username
    return AuthResponse(
        id=str(row.id),
        name=display,
        role=row.role,
        access_token=session_id,
        requires_password_change=bool(row.must_change_password),
    )


# ── Register ──────────────────────────────────────────────────────────────────

# POST /auth/register → cria uma conta nova de professor (devolve 201 Created).
@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=AuthResponse)
async def register(body: RegisterRequest, request: Request, conn: DbConn):
    username = body.email.lower().strip()

    # Impede contas duplicadas: se já existe alguém com este email, erro 409.
    existing = conn.execute(
        text("SELECT id FROM users WHERE username = :u LIMIT 1"),
        {"u": username},
    ).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com este email.",
        )

    pw_hash = hash_password(body.password)  # nunca se guarda a senha em claro, só o hash
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


# ── Student first access (self-registration) ────────────────────────────────

# POST /auth/student/status → diz ao ecrã de login se o aluno deve "entrar" ou
# "criar palavra-passe" (consoante já tenha conta ou só esteja na pauta).
@router.post("/student/status", response_model=StudentStatusResponse)
async def student_status(body: StudentStatusRequest, conn: DbConn):
    """Indica à UI de login se deve mostrar 'entrar' ou 'criar palavra-passe'."""
    number = body.student_number.strip()
    roster = conn.execute(
        text("SELECT id FROM students WHERE student_number = :sn LIMIT 1"),
        {"sn": number},
    ).fetchone()
    account = conn.execute(
        text("SELECT id FROM users WHERE username = :u AND role = 'estudante' LIMIT 1"),
        {"u": number.lower()},
    ).fetchone()
    return StudentStatusResponse(
        found_in_roster=roster is not None,
        has_account=account is not None,
    )


# POST /auth/student/activate → cria a conta do aluno no 1.º acesso, só se o
# número dele já constar da pauta (students). Liga a conta ao registo do aluno.
@router.post("/student/activate", status_code=status.HTTP_201_CREATED, response_model=AuthResponse)
async def student_activate(body: StudentActivateRequest, request: Request, conn: DbConn):
    """Cria a conta do estudante no primeiro acesso (validada contra a pauta)."""
    number = body.student_number.strip()
    if body.password != body.confirm_password:
        raise HTTPException(status_code=422, detail="As palavras-passe não coincidem.")
    if len(body.password) < 8 or not any(c.isupper() for c in body.password):
        raise HTTPException(status_code=422, detail="A palavra-passe não cumpre os requisitos mínimos.")

    student = conn.execute(
        text("SELECT id, full_name FROM students WHERE student_number = :sn LIMIT 1"),
        {"sn": number},
    ).fetchone()
    if not student:
        raise HTTPException(status_code=404, detail="Número de estudante não encontrado. Fala com o teu professor.")

    username = number.lower()
    existing = conn.execute(
        text("SELECT id FROM users WHERE username = :u LIMIT 1"),
        {"u": username},
    ).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail="Já existe uma conta. Faz login normalmente.")

    now = datetime.now(UTC).replace(tzinfo=None)
    pw_hash = hash_password(body.password)
    display = student.full_name or number
    result = conn.execute(
        text(
            "INSERT INTO users"
            " (username, password_hash, role, display_name, must_change_password,"
            "  is_active, created_at, updated_at)"
            " VALUES (:u, :ph, 'estudante', :dn, false, true, :now, :now) RETURNING id"
        ),
        {"u": username, "ph": pw_hash, "dn": display, "now": now},
    )
    user_id = result.scalar_one()
    # Link the students row to this user account
    conn.execute(
        text("UPDATE students SET user_id = :uid, updated_at = :now WHERE id = :sid"),
        {"uid": user_id, "now": now, "sid": student.id},
    )

    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    session_id = create_session(conn, user_id=user_id, ip_address=ip, user_agent=ua)
    conn.commit()

    LOGGER.info("student_activated", extra={"user_id": user_id, "student_number": number})
    return AuthResponse(
        id=str(user_id), name=display, role="estudante",
        access_token=session_id, requires_password_change=False,
    )


# ── Current user profile ────────────────────────────────────────────────────

# GET /auth/me → devolve o perfil de quem está autenticado (nome, papel, etc.).
# É o que o painel usa para saber quem entrou.
@router.get("/me", response_model=MeResponse)
async def me(request: Request, conn: DbConn):
    """Perfil resumido do utilizador autenticado (usado pelo painel)."""
    auth_header = request.headers.get("authorization", "")
    session_id = auth_header.removeprefix("Bearer ").strip() if auth_header.startswith("Bearer ") else None
    if not session_id:
        raise HTTPException(status_code=401, detail="Não autenticado.")
    now = datetime.now(UTC).replace(tzinfo=None)
    row = conn.execute(
        text(
            "SELECT u.id, u.display_name, u.username, u.role, u.disciplines"
            " FROM user_sessions us JOIN users u ON u.id = us.user_id"
            " WHERE us.id = :sid AND us.is_active = true AND us.expires_at > :now LIMIT 1"
        ),
        {"sid": session_id, "now": now},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Sessão expirada.")

    disciplines: list[str] = []
    if row.disciplines:
        try:
            disciplines = json.loads(row.disciplines)
        except (json.JSONDecodeError, TypeError):
            disciplines = []

    contexts_count = 0
    if row.role == "professor":
        cnt = conn.execute(
            text("SELECT count(*) FROM academic_contexts WHERE professor_id = :uid"),
            {"uid": row.id},
        ).fetchone()
        contexts_count = cnt[0] if cnt else 0
        # Se as disciplinas não estiverem guardadas no utilizador, deduz-las a
        # partir dos contextos. List comprehension: cria a lista das disciplinas
        # não-vazias encontradas.
        if not disciplines:
            drows = conn.execute(
                text("SELECT DISTINCT subject FROM academic_contexts WHERE professor_id = :uid"),
                {"uid": row.id},
            ).fetchall()
            disciplines = [d[0] for d in drows if d[0]]

    return MeResponse(
        id=str(row.id),
        name=row.display_name or row.username,
        role=row.role,
        disciplines=disciplines,
        contexts_count=contexts_count,
    )
