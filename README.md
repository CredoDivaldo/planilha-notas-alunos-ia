# Plataforma Académica

Plataforma local para gestão de notas académicas e divulgação de pautas via WhatsApp.

## Stack

- **Backend:** FastAPI (Python) + SQLite/Alembic migrations
- **Frontend:** React + Vite + TypeScript + Tailwind + shadcn/ui
- **Integração WhatsApp:** Evolution API (container Docker opcional)
- **Testes:** pytest (backend) · vitest (frontend)

Não há servidor Express legacy, não há UI single-page MVP antiga, não há bundlers Node.js para o backend. A API é exclusivamente FastAPI (`backend/app/`) e o cliente é exclusivamente Vite/React (`client/`).

## Quick start

### Opção 1: Unified Script (Recomendado)

```bash
./start-dev.sh
```

Este script bash arranca backend FastAPI + frontend Vite em paralelo. **Requer:**
- Python virtual environment (`.venv`) com dependências instaladas
- `npm run client:install` executado previamente

### Opção 2: npm run dev (Alternativo)

```bash
# Preparação única:
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
npm run client:install

# Depois, sempre use:
npm run dev
```

Este comando arranca backend e cliente em paralelo usando `concurrently`.

### Opção 3: Terminais separados (Debug)

```bash
# Terminal 1 — Backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
npm run dev:backend

# Terminal 2 — Frontend
npm run dev:client
```

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
| `./start-dev.sh` | **Recomendado:** Arranca backend + frontend em paralelo |
| `npm run dev` | Alternativa: arranca ambos (pode ter problemas de venv) |
| `npm run dev:backend` | Só backend (uvicorn com reload) |
| `npm run dev:client` | Só frontend (vite dev server) |
| `./setup-test-env.sh` | Registra utilizador de teste + valida auth (com backend a correr) |
| `npm run client:build` | Build de produção do frontend para `public/app/` |
| `pytest backend/tests/` | Suite pytest do backend |
| `npm run lint` | ESLint sobre testes frontend |

## Documentação

- Histórias e decisões de produto: `docs/stories/`
- Arquitectura do sistema: `docs/architecture/`
- Constitution e regras do framework AIOX: `.aiox-core/constitution.md`
