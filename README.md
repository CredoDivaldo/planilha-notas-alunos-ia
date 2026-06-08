# Plataforma Académica

Plataforma local para gestão de notas académicas e divulgação de pautas via WhatsApp.

## Stack

- **Backend:** FastAPI (Python) + SQLite/Alembic migrations
- **Frontend:** React + Vite + TypeScript + Tailwind + shadcn/ui
- **Integração WhatsApp:** Evolution API (container Docker opcional)
- **Testes:** pytest (backend) · vitest (frontend)

Não há servidor Express legacy, não há UI single-page MVP antiga, não há bundlers Node.js para o backend. A API é exclusivamente FastAPI (`backend/app/`) e o cliente é exclusivamente Vite/React (`client/`).

## Quick start

```bash
# Backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
npm run dev:backend

# Frontend (noutro terminal)
npm run client:install
npm run dev:client
```

Atalho unificado (a partir da raiz):

```bash
npm run dev
```

Este comando arranca backend e cliente em paralelo (`concurrently`).

## Estrutura

```
backend/        # FastAPI app, models, routes, migrations
client/         # Vite + React + TypeScript app
public/app/     # Build de produção do frontend (gerado por `npm run client:build`)
docs/           # Stories, arquitectura, PRDs
tests/          # Testes frontend e integração
legacy/         # Artefactos históricos preservados
```

## Comandos úteis

| Comando | Descrição |
|---------|-----------|
| `npm run dev` | Arranca backend + frontend em paralelo |
| `npm run dev:backend` | Só backend (uvicorn com reload) |
| `npm run dev:client` | Só frontend (vite dev server) |
| `npm run client:build` | Build de produção do frontend para `public/app/` |
| `pytest backend/tests/` | Suite pytest do backend |
| `npm run lint` | ESLint sobre testes frontend |

## Documentação

- Histórias e decisões de produto: `docs/stories/`
- Arquitectura do sistema: `docs/architecture/`
- Constitution e regras do framework AIOX: `.aiox-core/constitution.md`
