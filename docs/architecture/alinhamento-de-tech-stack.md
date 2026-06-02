# Alinhamento de Tech Stack

## Stack Existente

| Categoria | Tecnologia Actual | Versão | Uso na Melhoria | Notas |
|---|---|---:|---|---|
| Runtime backend legado | Node.js | definido pelo ambiente local | Mantido durante transição | `package.json` aponta `src/server.js` |
| Framework backend legado | Express | `^4.21.1` | Mantido para endpoints MVP | Separação actual em rotas e serviços |
| Frontend | HTML/CSS/JS estático | N/A | Mantido e evoluído | Servido por Express a partir de `public/` |
| CSV | `csv-parse` | `^5.5.6` | Mantido no legado; Python deve ter parser próprio | Não criar dependência cruzada JS/Python |
| Testes JS | Jest + Supertest | Jest `^29.7.0` | Mantidos para regressão MVP | `tests/critical-flow.test.js` cobre fluxo crítico |
| Qualidade JS | ESLint + TypeScript checker | ESLint `^9.26.0`, TS `^5.8.3` | Mantidos | `npm run quality` agrega gates |
| Persistência | JSON local | N/A | Legado/transitório | Não é fonte de verdade alvo |
| Integração externa | Evolution API | externa | Mantida | Canal WhatsApp principal |

## Novas Decisões Técnicas

| Tecnologia | Versão Alvo | Propósito | Racional | Integração |
|---|---:|---|---|---|
| Python | 3.12+ | Backend principal | Cumpre requisito do PRD e mantém stack madura | Novo pacote `backend/` |
| FastAPI | compatível com Python 3.12 | API web Python | Simples, local-first, bom suporte a Pydantic e OpenAPI | Entry point `backend/app/main.py` |
| Uvicorn | compatível com FastAPI | Servidor local ASGI | Padrão simples para desenvolvimento | `python -m uvicorn backend.app.main:app --reload` |
| SQLite | 3.x local | Base relacional local | Sem serviço externo, transaccional, adequado ao escopo local | Ficheiro `data/app.sqlite3` |
| SQLAlchemy | 2.x | Camada ORM/SQL | Boring tech com migrações e testes previsíveis | Repositórios Python |
| Alembic | 1.x | Migrações | Histórico de esquema versionado | Pasta `backend/migrations/` |
| Pydantic | 2.x | Schemas API | Contratos claros e validação | Schemas por módulo |
| pytest | 8.x | Testes Python | Padrão Python simples | `pytest backend/tests` |
| Ruff | versão actual estável | Lint/format Python | Ferramenta única e rápida | `ruff check backend` |
| mypy | versão actual estável | Typecheck Python | Mantém rigor em domínio académico | `mypy backend` |
