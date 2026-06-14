# ── Stage 1: Build frontend ──────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Install root deps (husky, etc.)
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Install client deps
COPY client/package.json client/package-lock.json ./client/
RUN npm --prefix client ci --ignore-scripts

# Copy source and build
COPY client/ ./client/
COPY public/ ./public/
COPY tsconfig.typecheck.json ./
RUN npm run client:build

# ── Stage 2: Python backend ───────────────────────────────────────────────────
FROM python:3.12-slim AS backend

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir \
    "fastapi>=0.115,<1" \
    "uvicorn[standard]>=0.30,<1" \
    "sqlalchemy>=2,<3" \
    "pydantic>=2,<3" \
    "argon2-cffi>=23,<25" \
    "python-multipart>=0.0.9,<1" \
    "httpx>=0.27,<1" \
    "anthropic>=0.28,<1" \
    "openai>=1.42,<2" \
    "alembic>=1.13,<2" \
    "python-dotenv>=1.0"

# Copy application code
COPY backend/ ./backend/
COPY alembic.ini ./
COPY --from=frontend-builder /app/public/ ./public/

# Ensure data directory exists for SQLite
RUN mkdir -p /app/data

ENV ACADEMIC_DATABASE_URL="sqlite:////app/data/app.sqlite3"
ENV PORT=8000

EXPOSE 8000

CMD ["sh", "-c", "PYTHONPATH=/app python /app/backend/init_db.py && uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
