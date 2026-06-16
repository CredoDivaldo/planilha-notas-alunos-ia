"""Calendar events router.

Routes under /api/v1/calendar (matches frontend paths):
  GET    /api/v1/calendar/events          — list all events for professor
  POST   /api/v1/calendar/events          — create event
  PUT    /api/v1/calendar/events/{id}     — update event
  DELETE /api/v1/calendar/events/{id}     — delete event
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text

LOGGER = logging.getLogger("backend.calendar")

router = APIRouter(prefix="/api/v1/calendar", tags=["calendar"])


def _get_user_id(request: Request) -> int:
    auth = request.headers.get("authorization", "")
    session_id = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else None
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado.")
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        from backend.app.config import get_settings
        from backend.app.database import build_engine
        engine = build_engine(get_settings().database_url)
    now = datetime.now(UTC).replace(tzinfo=None)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT user_id FROM user_sessions"
                " WHERE id = :sid AND is_active = true AND expires_at > :now LIMIT 1"
            ),
            {"sid": session_id, "now": now},
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada.")
    return int(row[0])


def _get_engine(request: Request):
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        from backend.app.config import get_settings
        from backend.app.database import build_engine
        engine = build_engine(get_settings().database_url)
    return engine


def _ensure_context_id_column(engine) -> None:
    """Add context_id column to calendar_events if it does not yet exist."""
    try:
        from sqlalchemy import inspect as sa_inspect
        inspector = sa_inspect(engine)
        cols = [c["name"] for c in inspector.get_columns("calendar_events")]
        if "context_id" not in cols:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE calendar_events ADD COLUMN context_id VARCHAR(120)"))
                conn.commit()
                LOGGER.info("calendar_events.context_id column added")
    except Exception as exc:
        LOGGER.warning("calendar_context_id_migration_failed", extra={"error": str(exc)})


class CalendarEventOut(BaseModel):
    id: str
    title: str
    date: str
    time: str | None = None
    type: str
    location: str | None = None
    endsAt: str | None = None
    context_id: str | None = None


class CalendarEventsResponse(BaseModel):
    events: list[CalendarEventOut]


class EventCreateRequest(BaseModel):
    title: str
    date: str
    type: str
    location: str | None = None
    endsAt: str | None = None
    context_id: str | None = None


class EventUpdateRequest(BaseModel):
    title: str | None = None
    date: str | None = None
    type: str | None = None
    location: str | None = None
    endsAt: str | None = None
    context_id: str | None = None


def _split_dt(value) -> tuple[str, str | None]:
    """Return (YYYY-MM-DD, HH:MM | None) from a datetime or timestamp string."""
    if value is None:
        return "", None
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d"), value.strftime("%H:%M")
    s = str(value)
    date = s[:10]
    time = s[11:16] if len(s) >= 16 else None
    # treat midnight as "no time"
    return date, (None if time in (None, "00:00") else time)


def _row_to_out(row) -> CalendarEventOut:
    date, time = _split_dt(row[2])
    ends_date, ends_time = _split_dt(row[5]) if row[5] else ("", None)
    return CalendarEventOut(
        id=str(row[0]),
        title=row[1] or "",
        date=date,
        time=time,
        type=row[3] or "outro",
        location=row[4] if row[4] else None,
        endsAt=(ends_time or ends_date) if row[5] else None,
        context_id=row[6] if len(row) > 6 and row[6] else None,
    )


@router.get("/events", response_model=CalendarEventsResponse)
async def list_events(request: Request) -> CalendarEventsResponse:
    user_id = _get_user_id(request)
    engine = _get_engine(request)
    _ensure_context_id_column(engine)
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, title, starts_at, event_type, location, ends_at, context_id"
                " FROM calendar_events"
                " WHERE created_by_user_id = :uid"
                " ORDER BY starts_at"
            ),
            {"uid": user_id},
        ).fetchall()
        return CalendarEventsResponse(events=[_row_to_out(r) for r in rows])


@router.post("/events", response_model=CalendarEventOut, status_code=status.HTTP_201_CREATED)
async def create_event(body: EventCreateRequest, request: Request) -> CalendarEventOut:
    user_id = _get_user_id(request)
    engine = _get_engine(request)
    _ensure_context_id_column(engine)
    now = datetime.now(UTC).replace(tzinfo=None)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "INSERT INTO calendar_events"
                " (title, starts_at, ends_at, event_type, location, context_id, created_by_user_id,"
                "  internal_status, created_at, updated_at)"
                " VALUES (:title, :starts, :ends, :etype, :loc, :ctx_id, :uid, 'published', :now, :now)"
                " RETURNING id"
            ),
            {
                "title": body.title,
                "starts": body.date,
                "ends": body.endsAt,
                "etype": body.type,
                "loc": body.location,
                "ctx_id": body.context_id,
                "uid": user_id,
                "now": now,
            },
        )
        new_id = result.scalar_one()
        conn.commit()
        row = conn.execute(
            text(
                "SELECT id, title, starts_at, event_type, location, ends_at, context_id"
                " FROM calendar_events WHERE id = :id"
            ),
            {"id": new_id},
        ).fetchone()
        return _row_to_out(row)


@router.put("/events/{event_id}", response_model=CalendarEventOut)
async def update_event(event_id: int, body: EventUpdateRequest, request: Request) -> CalendarEventOut:
    user_id = _get_user_id(request)
    engine = _get_engine(request)
    now = datetime.now(UTC).replace(tzinfo=None)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT id FROM calendar_events WHERE id = :eid AND created_by_user_id = :uid LIMIT 1"),
            {"eid": event_id, "uid": user_id},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Evento não encontrado.")
        updates: dict = {"now": now, "eid": event_id}
        set_clauses = ["updated_at = :now"]
        if body.title is not None:
            updates["title"] = body.title
            set_clauses.append("title = :title")
        if body.date is not None:
            updates["starts"] = body.date
            set_clauses.append("starts_at = :starts")
        if body.endsAt is not None:
            updates["ends"] = body.endsAt
            set_clauses.append("ends_at = :ends")
        if body.type is not None:
            updates["etype"] = body.type
            set_clauses.append("event_type = :etype")
        if body.location is not None:
            updates["loc"] = body.location
            set_clauses.append("location = :loc")
        if body.context_id is not None:
            updates["ctx_id"] = body.context_id
            set_clauses.append("context_id = :ctx_id")
        conn.execute(
            text(f"UPDATE calendar_events SET {', '.join(set_clauses)} WHERE id = :eid"),
            updates,
        )
        conn.commit()
        updated = conn.execute(
            text(
                "SELECT id, title, starts_at, event_type, location, ends_at, context_id"
                " FROM calendar_events WHERE id = :eid"
            ),
            {"eid": event_id},
        ).fetchone()
        return _row_to_out(updated)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, request: Request) -> None:
    user_id = _get_user_id(request)
    engine = _get_engine(request)
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM calendar_events WHERE id = :eid AND created_by_user_id = :uid"),
            {"eid": event_id, "uid": user_id},
        )
        conn.commit()
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Evento não encontrado.")
