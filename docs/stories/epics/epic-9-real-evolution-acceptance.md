# Epic 9 — Real-Evolution Acceptance Run

**Status:** Ready
**Owner:** @dev
**Priority:** P0
**Points Total:** 10
**Created:** 2026-06-08
**Created by:** @pm (Morgan)
**Plan:** `/Users/user/.claude-piramyd/plans/delightful-noodling-river.md`
**Predecessor:** Epic 8 (Production Cutover) — merged at `d6e452a`

---

## Overview

O Epic 6 (AI WhatsApp Chatbot, 2026-06-02) shipped com QA Gate PASS, mas o engine só correu em **dry-run tests**. Nunca foi exercitado contra uma instância real da Evolution API. Após o Epic 8, toda a plumbing de integração está no sítio (FastAPI em :8000, `EvolutionApiClient` em `backend/app/services/evolution_api_client.py`, webhook em `POST /api/v1/chatbot/webhook`). O último buraco não verificado é: **o chatbot recebe mesmo uma mensagem WhatsApp e responde?**

Este Epic 9 fecha o último gap de aceitação de produção, com 3 stories sequenciais: bring-up da stack Evolution real + smoke E2E com WhatsApp real, chaos test mid-broadcast, e runbook operacional.

---

## Business Context

Sem este Epic, o chatbot de IA cumpre o requisito externo da disciplina (modelo de linguagem real chamado) mas nunca foi provado em condições reais — só com mocks. Para credibilizar a entrega e preparar a operação pós-disciplina, precisamos:

- Prova viva de que `EvolutionApiClient` (Epic 6) + `POST /api/v1/chatbot/webhook` + Baidu QianFan realmente entregam um loop WhatsApp → IA → WhatsApp.
- Confiança de que o sistema recupera de uma falha de Evolution a meio de um broadcast (não perda silenciosa de mensagens).
- Documentação operacional para Credo (ou sucessor) poder: subir a stack, parear um número, rodar as chaves, diagnosticar falhas.

---

## Scope

### IN — O que este Epic entrega

- `docker-compose.evolution.yml` (Redis + Postgres + Evolution API em :8080) trazido up e validado em localhost
- `.env.evolution` com `BAIDU_API_KEY` (free tier QianFan) configurado **Revised 2026-06-08:** `.env.evolution` não contém IA (IA vive no FastAPI). Root `.env` traz `DEEPSEEK_API_KEY` + `AI_PROVIDER=deepseek` + `AI_MODEL=deepseek-chat` (definidos em Story 9.0).
- Root `.env` com `EVOLUTION_BASE_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE`, `CHATBOT_WEBHOOK_TOKEN` preenchidos
- Webhook Evolution → FastAPI configurado para `http://localhost:8000/api/v1/chatbot/webhook`
- Um número de teste WhatsApp pareado (one-time human step via QR)
- Smoke E2E com mensagem real: segunda pessoa → FastAPI → DeepSeek → Evolution → resposta visível na segunda pessoa
- Transcript completo arquivado em `docs/qa/evolution-acceptance-9.1.md`
- Chaos test: kill Evolution mid-broadcast, verificar 502 sanitized + recoverability
- Edge case de rate-limiting (11ª mensagem do dia) verificado
- Runbook operacional `docs/runbooks/evolution.md` com bring-up, pairing, rotação de chaves, failure modes, log locations, backup/restore do volume Postgres

### OUT — O que este Epic NÃO entrega

- UI ou portal frontend novo (Epic 7/10 cobrem)
- Trocar Baidu QianFan por outro provider (Epic 6 fixou Baidu; mudança → novo epic) **Resolved 2026-06-08:** troca para DeepSeek foi feita via Story 9.0 dentro do Epic 9.
- Persistência de histórico de conversas multi-turno (Epic 6 OUT)
- Suporte a media (imagens, documentos) — WhatsApp permite, chatbot não usa
- Hardening de produção multi-instância (single-node only)
- Testes de carga (load test com 100+ broadcasts)
- Migração para Evolution API v2 (se sair entre Epic 9 e 10)

---

## Success Criteria

| Critério | Métrica |
|----------|---------|
| Stack Evolution local up | `docker ps` mostra `evolution_api`, `evolution_redis`, `evolution_postgres` healthy |
| Webhook live | Evolution instance `webhook` configurada para `http://localhost:8000/api/v1/chatbot/webhook` |
| E2E real | Mensagem WhatsApp enviada de nº B → recebida por FastAPI → respondida via Evolution → visível em nº B |
| Transcript documentado | `docs/qa/evolution-acceptance-9.1.md` com timestamps, payloads, response |
| Chaos test passa | Mid-broadcast kill do Evolution → FastAPI retorna 502 com erro sanitizado; retry recupera |
| Rate-limit edge case | 11ª mensagem do dia é bloqueada (HTTP 429 ou resposta educada) |
| Runbook runnable | `docs/runbooks/evolution.md` cobre os 6 tópicos do scope IN, Credo consegue seguir sem ajuda |
| Qualidade mantida | `npm run quality` (lint + typecheck + jest) verde; `pytest backend/tests` verde |

---

## Stories

| ID | Título | Points | Priority | Owner | Quality Gate | Depends On |
|----|--------|--------|----------|-------|--------------|-----------|
| 9.1 | Boot Evolution + send real WhatsApp test message | 5 | P0 | @dev | @qa | — |
| 9.2 | Chaos test (Evolution mid-broadcast) | 3 | P0 | @dev | @qa | 9.1 |
| 9.3 | Production runbook | 2 | P1 | @dev | @qa | 9.1 |
| **TOTAL** | | **10** | | | | |

**Ordem de merge:** 9.1 → 9.2 → 9.3 (9.2 e 9.3 podem correr em paralelo APÓS 9.1 estar Done, mas 9.3 só fecha o Epic com utilidade real depois de 9.1 + 9.2 — recommend sequential).

---

## Dependencies

### Prerequisites (bloqueantes)

- **Epic 6 — AI WhatsApp Chatbot** deve estar completo (Done desde 2026-06-02)
  - `backend/app/services/evolution_api_client.py` — `EvolutionApiClient` com `send_text`, `connection_state`, etc.
  - `backend/app/routers/chatbot.py` — `POST /api/v1/chatbot/webhook` handler
  - `backend/app/portal/routes.py` — chatbot context builder
  - Rate-limiting por telefone (Story 3.4) — já em produção
  - Error sanitization (Story 3.6) — base do comportamento esperado em 9.2

- **Epic 8 — Production Cutover** deve estar completo (master em `d6e452a`)
  - `docker-compose.evolution.yml` já existe no repo
  - `.env.evolution.example` já existe
  - FastAPI production-ready em :8000

### Recursos externos (humanos / contas)

- **Número de teste WhatsApp** (real) — Credo deve providenciar (single-use recomendado; ver Pre-flight abaixo)
- **Conta Baidu QianFan free-tier** — Credo deve criar e obter `BAIDU_API_KEY` **Replaced 2026-06-08:** agora **Conta DeepSeek** — Credo cria em https://platform.deepseek.com/api_keys e obtém `DEEPSEEK_API_KEY` (já existe no `.env` raiz linha 15).
- **Segundo telefone** (pessoal de Credo ou tester) para enviar a mensagem de teste em 9.1

### Inter-Story

- **9.1** é prerequisito de 9.2 e 9.3 (precisamos de Evolution live para testar chaos e documentar runbook com base no que realmente funciona)
- **9.2** e **9.3** podem correr em paralelo (9.3 é puramente docs, não compete por recursos com 9.2)
- **9.3** idealmente fica com a "última actualização" do runbook depois de 9.2 revelar gotchas

---

## Pre-flight (manual, antes de 9.1)

Credo precisa de:
1. **Número de teste WhatsApp** — pode ser pessoal com consentimento, ou um nº descartável pré-pago. Single-use recomendado (não vazar número de produção).
2. **Conta Baidu QianFan free-tier** — `https://cloud.baidu.com/` → Console QianFan → criar API key (grátis até volume razoável). Guardar como `BAIDU_API_KEY` em `.env.evolution`. **Replaced 2026-06-08:** agora **Conta DeepSeek** — `https://platform.deepseek.com/api_keys` → criar API key. Guardar como `DEEPSEEK_API_KEY` no root `.env` (linha 15 já preparada; já existe no `.env` actual).
3. **Decisão sobre persistência do número** — single-use (recomendado) ou persistente. Se persistente, documentar em `docs/runbooks/evolution.md` (entra no scope de 9.3).

Estes são os **únicos** blockers humanos. Tudo o resto é automatizado via AIOX SDC engine.

---

## Sprint Timeline

- **Sprint 1 (proposto):** Story 9.1 (5 pts) — inclui bring-up + E2E real com WhatsApp
- **Sprint 2 (proposto):** Stories 9.2 (3 pts) ∥ 9.3 (2 pts) — chaos test + runbook

Sequência crítica: 9.1 → (9.2 ∥ 9.3). Total: ~10 pontos em ~2 sprints (5 dias úteis cada), assumindo 1 ponto ≈ 0.5 dia.

---

## Critical Path

```
Story 9.1 (bring-up + E2E real)
    │
    ├──► Story 9.2 (chaos test)
    │
    └──► Story 9.3 (runbook)
```

- 9.1 é o **critical path** (única story sequencial obrigatória no início)
- 9.2 e 9.3 podem paralelizar-se, mas 9.3 é mais rico se vier depois de 9.2
- **Total end-to-end se sequencial:** 5 + 3 + 2 = 10 pontos
- **Total end-to-end se paralelizado (9.2 ∥ 9.3):** 5 + max(3, 2) = 8 pontos efectivos

---

## Risk Mitigation

**Primary Risk:** Credo não providencia nº WhatsApp de teste a tempo → Epic 9 bloqueia indefinidamente em 9.1.

**Mitigation:**
- Pre-flight explícito acima; `*create-epic` activa o reminder
- Fallback documentado: se nº real não disponível, 9.1 pode usar o `mock` mode (de Epic 6) **mas** o Epic 9 explicitamente rejeita isso — o ponto é o teste *real*. Em último caso, marcar Epic 9 como `Blocked` e parar o SDC.

**Secondary Risk:** Evolution API v1 fica deprecated entre Epic 9 e 10 → webhook muda de contrato.

**Mitigation:**
- Story 9.3 (runbook) documenta a versão da Evolution API usada
- 9.1 deve fixar a tag de imagem (`:1.x.y`) no `docker-compose.evolution.yml` em vez de `:latest`
- OUT-of-scope explícito: migração para v2

**Tertiary Risk:** Chaos test em 9.2 quebra a base de dados Evolution Postgres ao kill o container a meio de transacção.

**Mitigation:**
- Volume Postgres do Evolution é separado (Docker volume) — `docker kill` não corrompe (Postgres é ACID)
- Runbook (9.3) documenta recovery: `docker compose restart evolution_postgres` + verificar `pg_isready`
- Story 9.1 já traz a stack up com healthchecks, então 9.2 tem baseline de "saudável" para comparar

---

## Compatibility Requirements

- [ ] Endpoints FastAPI existentes permanecem unchanged (`/api/v1/chatbot/webhook` já existe desde Epic 6)
- [ ] `EvolutionApiClient` não muda de contrato — só é exercitado em condições reais pela primeira vez
- [ ] Zero mudanças no schema SQLite (`backend/app/app.sqlite3`)
- [ ] Zero mudanças em frontend (`client/src/**`) — Epic 7 não é tocado
- [ ] `docker-compose.evolution.yml` já existe; Epic 9 só documenta como usá-lo, não o modifica (a menos que healthcheck falhe em 9.1, aí 9.3 pode sugerir fix no compose)

---

## Definition of Done (Epic-level)

- [ ] 3 stories marcadas como `Done` em `docs/stories/`
- [ ] `docs/qa/evolution-acceptance-9.1.md` existe com transcript real
- [ ] `docs/runbooks/evolution.md` cobre bring-up, pairing, rotação de chaves, failure modes, log locations, backup/restore
- [ ] `npm run quality` verde; `pytest backend/tests` verde
- [ ] 3 PRs merged em `master` com mensagens conventional commit
- [ ] `docs/architecture/architecture.md` actualizado com referência à stack Evolution local
- [ ] Credo confirma (human sign-off) que o loop E2E WhatsApp real funciona

---

## Change Log

| Date | Author | Change |
|------|--------|--------|
| 2026-06-08 | @pm (Morgan) | Epic criado a partir do plan `delightful-noodling-river.md` (seção Epic 9) e do handoff `.remember/remember.md` |
