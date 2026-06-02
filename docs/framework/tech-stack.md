# Tech Stack Handoff

**Status:** fonte curta de handoff; `docs/architecture.md` é a fonte decisória principal.

## Stack Actual Preservada

- Node.js + Express 4 para o MVP legado.
- Frontend estático em `public/`.
- JSON local em `data/` como persistência legado/transitória.
- Jest + Supertest para testes de regressão.
- ESLint e TypeScript checker por `tsc --noEmit`.
- Evolution API por HTTP/Docker Compose como integração WhatsApp.

## Stack Alvo Epic 5

- Python 3.12+.
- FastAPI em `backend/app/main.py`.
- Uvicorn para execução local.
- SQLite em `data/app.sqlite3`.
- SQLAlchemy 2.x.
- Alembic em `backend/migrations/`.
- Pydantic 2.x.
- pytest, Ruff e mypy quando `backend/` existir.

## Local-First

Cloud, CI/CD remoto, canary, blue/green e produção multiambiente são N/A para esta fase. A validação obrigatória é local e por story.
