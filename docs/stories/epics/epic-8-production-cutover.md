# Epic 8 — Production Cutover & Hardening

**Status:** Ready
**Owner:** @dev
**Priority:** P0
**Points Total:** 24
**Created:** 2026-06-07
**Created by:** @pm (Morgan)
**Plan:** `/Users/user/.claude-piramyd/plans/delightful-noodling-river.md`

---

## Overview

Os 9 stories do Epic 7 (frontend React/Vite) estão merged em `master` como "Done" e o Epic 6 (chatbot WhatsApp) tem QA Gate PASS, mas `npm run dev` continua a servir a UI monopágina antiga do MVP (`public/index.html`) e o backend Express legado (`src/`) continua a correr em :3000. O utilizador viu a nova UI React via "professor demo" — que funcionou apenas porque o `DashboardPage.tsx` tem try/catch + fallbacks para mock data.

**Decisão do utilizador (2026-06-07):** manter só FastAPI + React, remover tudo o que é do MVP Express legado.

Este Epic fecha os 3 buracos de produção:
1. Os 4 endpoints que faltam no FastAPI (students/grades upload, match, broadcast, WhatsApp lifecycle)
2. A unificação de `npm run dev` para servir a nova UI
3. A remoção limpa do tree Express + JSONs legados

---

## Business Context

Sem este Epic, a app corre em modo de demo frágil (try/catch + mock data) e o backend Express morto (`src/`) é dead weight. Cutover em produção exige:
- Endpoints reais no FastAPI (substituir os 4 que o frontend já tenta chamar)
- `npm run dev` unificado que arranca Vite + uvicorn
- Remoção do tree Express para evitar regressões acidentais (alguém a editar `src/server.js` em vez do FastAPI)
- Smoke tests E2E (substituem os `WAIVER` em testes do Epic 7)

---

## Scope

### IN — O que este Epic entrega

- 2 novos routers FastAPI: `ingest.py` (upload students/grades) + `professor.py` (match, broadcast, whatsapp)
- Reutilização de `PublicationService` e `EvolutionApiClient` (Epic 6) via thin adapters
- Vite proxy `:5173 → :8000` (substitui o proxy morto `:3000`)
- `npm run dev` unificado via `concurrently` (Vite 5173 + uvicorn 8000)
- Subcommand CLI `migrate-legacy-csv` para re-importar CSVs de demo
- Movimentação de `data/*.json` → `legacy/data/` e `data/*.csv` → `legacy/fixtures/`
- Remoção completa do tree Express (`src/`, `public/index.html`, `public/app.js`, `public/styles.css`, testes Express)
- Limpeza de deps Express em `package.json` (cors, csv-parse, dotenv, express, express-rate-limit, multer)
- Suite Playwright smoke (cobre happy path + regressões de cutover)
- Cutover checklist human-runnable (curl copy-paste)
- Testes de regressão Python (TestClient confirma 404 nos paths antigos)

### OUT — O que este Epic NÃO entrega

- Exercício Epic 6 contra Evolution real → **Epic 9**
- UI rebuild com shadcn primitives + Lucide, remoção de emojis → **Epic 10**
- PWA / i18n / Storybook → backlog pós-Epic 10
- Investigação de `academic.db` (raiz 0 bytes) vs `backend/app/app.sqlite3` → backlog

---

## Stories

| ID | Título | Points | Priority | Owner | Quality Gate | Depends On |
|----|--------|--------|----------|-------|--------------|-----------|
| 8.1 | Port CSV ingest endpoints to FastAPI | 5 | P0 | @dev | @qa | — |
| 8.2 | Port match + broadcast + WhatsApp lifecycle | 8 | P0 | @dev | @qa | 8.1 |
| 8.3 | Vite proxy + unified dev script | 2 | P0 | @dev | @qa | 8.1, 8.2 |
| 8.4 | Storage cutover (data/*.json → DB) | 2 | P1 | @dev | @qa | 8.1 |
| 8.5 | Remove legacy Express tree | 2 | P0 | @dev | @qa | 8.1, 8.2, 8.3, 8.4 |
| 8.6 | Playwright smoke + cutover verification | 5 | P0 | @dev | @qa | 8.5 |
| **TOTAL** | | **24** | | | | |

**Ordem de merge:** 8.1 → 8.2 → (8.3 ∥ 8.4) → 8.5 → 8.6

---

## Dependencies

### Prerequisites (bloqueantes)

- **Epic 5 — Academic Platform Foundation** deve estar completo
  - `backend/app/models/academic.py` (ClassEnrollment, GradeEntry) — necessário para Story 8.1
  - `backend/app/publication/service.py` (PublicationService) — necessário para Story 8.2
  - `backend/app/services/evolution_api_client.py` (EvolutionApiClient) — necessário para Story 8.2

- **Epic 6 — AI WhatsApp Chatbot** deve estar completo
  - `EvolutionApiClient` com métodos `connection_state()` — necessário para Story 8.2

- **Epic 7 — Frontend da Plataforma** deve estar completo
  - `client/src/pages/professor/DashboardPage.tsx` — alvo de cleanup em 8.1, 8.2
  - `client/src/pages/professor/PublishPage.tsx` — alvo de cleanup em 8.2
  - `client/vite.config.ts` — alvo de mudança em 8.3

### Inter-Story

- **8.1** é prerequisito de 8.2, 8.3, 8.4, 8.5
- **8.2** é prerequisito de 8.3, 8.5
- **8.3** e **8.4** podem correr em paralelo (não há dependência entre si)
- **8.5** é bloqueado por 8.1, 8.2, 8.3, 8.4
- **8.6** é bloqueado por 8.5

---

## Cutover Decisions (aprovadas pelo utilizador em 2026-06-07)

| Decisão | Escolha | Razão |
|---|---|---|
| Endpoints em falta no FastAPI | **Portar como routers FastAPI novos** (`backend/app/routers/ingest.py` + `backend/app/routers/professor.py`) | Rejeitado: sidecar Node (viola "no Express"); remoção da UI (mata o professor demo) |
| `npm run dev` unificado | **Vite proxy → FastAPI :8000** via `concurrently` | Único mental model. Sem Express, sem static-serve-from-FastAPI |
| `data/*.json` | Mover para `legacy/data/` via `git mv` | JSONs já só são lidos pelo Express morto |
| `outputs/` (wireframes, design-system) | **Manter** | Decisão do utilizador (referência UX) |
| `academic.db` (raiz 0 bytes) | Investigar depois; Epic 8 não mexe | Decisão do utilizador |
| Epic 6 acceptance run (Evolution real) | **Epic 9 separado** | Não confundir code cutover com live integration |
| Playwright smoke tests | **Dentro do Epic 8** (Story 8.6) | Cobertura do cutover, fecha os `WAIVER` do Epic 7 |

---

## Definition of Done (Epic-level)

- [ ] As 6 stories marcadas como `Done` no `docs/stories/`
- [ ] `git grep "express\|src/server.js"` retorna 0 matches em código de produção
- [ ] `git grep "data/students.json\|data/grades-last-upload\|data/match-last"` retorna 0 matches em código não-legacy
- [ ] `npm run quality` (lint + typecheck + jest) verde
- [ ] `pytest backend/tests` verde
- [ ] `npm run dev` arranca Vite (5173) + FastAPI (8000) sem erro
- [ ] `http://localhost:5173/` mostra a nova UI React (não `public/index.html`)
- [ ] `npm run e2e` (Playwright) verde
- [ ] 6 PRs merged em `master` com mensagens conventional commit
- [ ] `docs/runbooks/dev.md` documenta o novo `npm run dev`
- [ ] `docs/architecture/architecture.md` secção "Storage" actualizada
- [ ] `docs/qa/cutover-checklist.md` criado e runnable por humanos

---

## Risk Mitigation

**Primary Risk:** A remoção do tree Express em 8.5 pode quebrar testes ou código de import que ainda dependam de paths Express.

**Mitigation:**
- Stories 8.1 + 8.2 portam todos os endpoints *antes* de 8.5 remover o tree
- Story 8.5 deve fazer `git grep` por referências Express antes de fazer `git rm` para garantir zero código activo
- Story 8.6 cobre as regressões de cutover (GET /api/students/upload deve retornar 404, POST /api/v1/students/upload sem auth deve retornar 401)
- Rollback Plan: cada story é merged num PR individual; se 8.5 falhar, `git revert` do PR restaura o tree

**Secondary Risk:** Vite proxy caching pode fazer o browser continuar a chamar :3000 mesmo após 8.3 mudar para :8000.

**Mitigation:** Documentar em `docs/runbooks/dev.md` a limpeza de `node_modules/.vite` cache se houver comportamento estranho.

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-06-07 | @pm (Morgan) | Epic criado a partir do plan `delightful-noodling-river.md` |
