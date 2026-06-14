from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import os

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict

from backend.app.config import Settings, get_settings
from backend.app.database import build_engine, ensure_sqlite_directory, inspect_sqlite_runtime
from backend.app.portal.routes import router as portal_router
from backend.app.routers.academic_contexts import router as academic_contexts_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.calendar import router as calendar_router
from backend.app.routers.chatbot import router as chatbot_router
from backend.app.routers.delegado import router as delegado_router
from backend.app.routers.grades import router as grades_router
from backend.app.routers.ingest import router as ingest_router
from backend.app.routers.professor import router as professor_router
from backend.app.routers.whatsapp_setup import router as whatsapp_setup_router

LOGGER = logging.getLogger("backend.app")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")


class HealthResponse(BaseModel):
    status: str
    service: str
    api_prefix: str
    database: dict[str, str | bool]
    request_id: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from sqlalchemy.orm import sessionmaker
    from backend.app.models import Base

    settings = getattr(app.state, "settings", None) or get_settings()
    ensure_sqlite_directory(settings.database_url)
    engine = build_engine(settings.database_url)
    app.state.settings = settings
    app.state.engine = engine
    app.state.database_runtime = inspect_sqlite_runtime(engine)
    app.state.session_factory = sessionmaker(bind=engine)

    # Alembic migrations run before uvicorn starts (see Dockerfile CMD).
    # create_all covers any ORM-only models not in migrations (idempotent).
    Base.metadata.create_all(engine)

    LOGGER.info(
        "backend_startup",
        extra={
            "database_url": settings.database_url,
            "database_runtime": app.state.database_runtime,
        },
    )
    try:
        yield
    finally:
        engine.dispose()


async def request_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Any]],
) -> Any:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        LOGGER.exception("request_failed", extra={"request_id": request_id})
        raise
    response.headers["X-Request-ID"] = request_id
    return response


def _request_id_from(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    app = FastAPI(title=resolved_settings.app_name, version="0.1.0", lifespan=lifespan)
    app.state.settings = resolved_settings
    app.middleware("http")(request_id_middleware)

    # Auth router — login, register, change-password
    app.include_router(auth_router)

    # Register portal router (AC-1: read-only student portal)
    app.include_router(portal_router)

    # Register chatbot router (Story 6.1+: WhatsApp webhook)
    app.include_router(chatbot_router)

    # Register ingest router (Story 8.1: legacy CSV upload endpoints)
    app.include_router(ingest_router)

    # Register professor router (Story 8.2: match / broadcast / WhatsApp)
    app.include_router(professor_router)

    # Academic contexts CRUD (missing routes — sprint fix)
    app.include_router(academic_contexts_router)

    # Grades router (missing routes — sprint fix)
    app.include_router(grades_router)

    # Calendar events router (missing routes — sprint fix)
    app.include_router(calendar_router)

    # Delegado portal router (missing routes — sprint fix)
    app.include_router(delegado_router)

    # Per-professor WhatsApp instance setup
    app.include_router(whatsapp_setup_router)

    # Health endpoint — must be registered BEFORE the SPA catch-all below
    @app.get(f"{resolved_settings.api_prefix}/health", response_model=HealthResponse)
    async def health(request: Request) -> HealthResponse:
        database_runtime = getattr(request.app.state, "database_runtime", None)
        if database_runtime is None:
            engine = build_engine(resolved_settings.database_url)
            try:
                database_runtime = inspect_sqlite_runtime(engine)
            finally:
                engine.dispose()

        return HealthResponse(
            status="ok",
            service=resolved_settings.app_name,
            api_prefix=resolved_settings.api_prefix,
            database=database_runtime,
            request_id=_request_id_from(request) or "",
        )

    # Serve built frontend static files (production: public/app).
    # The SPA catch-all /{full_path:path} must come LAST so it never shadows API routes.
    static_dir = os.path.join(os.path.dirname(__file__), "..", "..", "public", "app")
    static_dir = os.path.abspath(static_dir)
    if os.path.isdir(static_dir):
        # Mount /assets and /favicon.svg explicitly so the browser can load them.
        assets_dir = os.path.join(static_dir, "assets")
        if os.path.isdir(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="spa-assets")

        _API_PREFIXES = ("api/", "auth/", "whatsapp/", "students/", "grades/",
                         "broadcast/", "academic-contexts/", "portal/")

        @app.get("/", include_in_schema=False)
        async def root_redirect() -> FileResponse:
            return FileResponse(os.path.join(static_dir, "index.html"))

        @app.get("/{full_path:path}", include_in_schema=False)
        async def spa_fallback(full_path: str) -> FileResponse:
            from fastapi import HTTPException as _HTTPException
            if full_path.startswith(_API_PREFIXES):
                raise _HTTPException(status_code=404)
            # Serve real static files (favicon, icons, manifests) if they exist.
            candidate = os.path.join(static_dir, full_path)
            if os.path.isfile(candidate):
                return FileResponse(candidate)
            # Everything else is a React Router path → return index.html.
            return FileResponse(os.path.join(static_dir, "index.html"))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = _request_id_from(request)
        LOGGER.exception("unhandled_api_error", extra={"request_id": request_id})
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                code="internal_error",
                message="Unexpected internal error.",
                request_id=request_id,
            ).model_dump(exclude_none=True),
        )

    return app


app = create_app()
