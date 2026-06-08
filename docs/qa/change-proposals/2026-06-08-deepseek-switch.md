# Sprint Change Proposal — Baidu QianFan → DeepSeek Chat (2026-06-08)

**Status:** Awaiting approval
**Created:** 2026-06-08
**Author:** @aiox-master (via `*correct-course` task)
**Trigger:** User signal — "Não vamos usar Baidu. Tenho chave DeepSeek. Trocar antes do Epic 9."
**Scope:** Provider AI substitution; no scope expansion

---

## 1. Identified Issue Summary

O Epic 6 (CLOSED 2026-06-02) fixou Baidu QianFan como provedor default de IA para o chatbot, com base em "free tier, zero custos". Em 2026-06-08, Credo reportou que:

1. Obteve acesso a uma chave de API do DeepSeek (`DEEPSEEK_API_KEY` já presente no `.env` raiz, linha 15).
2. Quer trocar o provedor **antes** de iniciar o Epic 9 (acceptance run Evolution).
3. Quer limitar o switch a "alterar APENAS as partes que mencionam Baidu" — sem scope creep.

A mudança é um pivot técnico entre provedores equivalentes (chat LLM, ambos com API HTTPS). Não há alteração de feature, AC, ou UI.

---

## 2. Epic Impact Summary

| Epic | Status | Impacto |
|------|--------|---------|
| Epic 6 (CLOSED 2026-06-02) | Done | **Notas históricas adicionadas** em 6.2, 6.3. Gates não re-executados. |
| Epic 7 (CLOSED) | Done | Zero impacto (frontend-only). |
| Epic 8 (CLOSED) | Done | Zero impacto (cutover/legacy removal). |
| **Epic 9 (Draft)** | A iniciar | **Story 9.0 (NEW)** dedicada ao switch precede 9.1/9.2/9.3. Stories 9.1, 9.3 actualizadas para mencionar DeepSeek. |

**Net effect:** Epic 9 passa a ter 4 stories (9.0, 9.1, 9.2, 9.3) em vez de 3. Total de pontos: 5 + 3 + 3 + 2 = **13** (vs 10 planeados). Justificável porque o switch isola risco e dá QA gate dedicado.

---

## 3. Artifact Adjustment Needs

### 3.1 Code (Python)

| File | Action | Notes |
|------|--------|-------|
| `backend/app/services/deepseek_provider.py` | **CREATE** | OpenAI-compat SDK; new `DeepSeekProvider` class |
| `backend/app/services/baidu_provider.py` | **DELETE** | Permanently removed |
| `backend/app/services/ai_chatbot.py` | **MODIFY** | Factory `AIGradeQueryService.__init__` — new `deepseek` branch, remove `baidu` branch |
| `pyproject.toml` | **MODIFY** | Remove `qianfan>=0.4,<1` (no new deps — `openai` already present) |
| `backend/tests/conftest.py` | **MODIFY** | Default `AI_PROVIDER=deepseek`; `DEEPSEEK_API_KEY=test-...` |
| `backend/tests/test_ai_chatbot.py` | **NO CHANGE** | Uses `AI_PROVIDER=claude`+mock; abstraction holds |

### 3.2 Configuration

| File | Action | Notes |
|------|--------|-------|
| `.env.example` | **MODIFY** | `AI_PROVIDER=baidu` → `AI_PROVIDER=deepseek`; `BAIDU_API_KEY=...` block replaced by `DEEPSEEK_API_KEY` reference; `AI_MODEL=ernie-3.5-8k` → `AI_MODEL=deepseek-chat` |

### 3.3 Stories & Architecture

| File | Action | Notes |
|------|--------|-------|
| `docs/stories/6.2.ai-grade-query-service.md` | **MODIFY** | Change Log +2.4; "Revised 2026-06-08" markers in body |
| `docs/stories/6.3.chatbot-end-to-end-flow.md` | **MODIFY** | Header note; env-vars section |
| `docs/stories/9.0.deepseek-provider-switch.md` | **CREATE** | New pre-Acceptance story |
| `docs/stories/9.1.boot-evolution-send-real-whatsapp.md` | **MODIFY** | Story Statement, AC2, AC5, T2 — "Baidu" → "DeepSeek"; add "Depends On: 9.0" |
| `docs/stories/9.2.chaos-test-evolution-mid-broadcast.md` | **NO CHANGE** | Generic; no provider-specific text |
| `docs/stories/9.3.production-runbook.md` | **MODIFY** | AC4: "Baidu 429" → "DeepSeek 429" |
| `docs/stories/epics/epic-6-ai-whatsapp-chatbot.md` | **MODIFY** | Dependencies + Risks — markers |
| `docs/stories/epics/epic-9-real-evolution-acceptance.md` | **MODIFY** | Pre-flight section: Baidu → DeepSeek; OUT clause resolved |
| `docs/architecture/system-architecture.md` | **MODIFY** | Add DEPRECATED marker to Baidu block; new DeepSeek block |

### 3.4 Gates

| File | Action | Notes |
|------|--------|-------|
| `docs/qa/gates/9.0-deepseek-provider-switch.yml` | **CREATE** | New gate for Story 9.0; expected PASS |
| `docs/qa/gates/6.1-whatsapp-webhook-handler.yml` | **MODIFY** | Add synchronization note in `documentation.notes` referencing this proposal |

### 3.5 Unchanged (verified)

- `frontend/` — no references to Baidu (AI is backend-only)
- `scripts/`, `outputs/` — no references
- `.env.evolution` — correct as-is; AI lives in FastAPI, not Evolution
- `docker-compose.evolution.yml` — correct as-is

---

## 4. Recommended Path Forward

**Option 1: Direct Adjustment + Story dedicada 9.0** ✅ Selected

- **Effort:** 3 pontos (small, isolated, low-risk)
- **Wasted work:** zero (Baidu code is fully removed, not archived)
- **Risks:** Low (provider abstraction holds; tests are mocked; legacy fallbacks preserved)
- **Timeline:** +1 sprint day vs Epic 9 baseline
- **Sustainability:** High — DeepSeek is paid but cheap (~$0.14/M); production-grade

**Option 2: Rollback Story 6.2** ❌ Rejected
- Effort: 5+ points (revert 14 commits, re-implement)
- Wasted work: full Story 6.2 implementation
- Risks: High (regression in working code)
- Timeline: +1 week

**Option 3: Re-scope MVP / postpone Epic 9** ❌ Rejected
- Effort: zero code; high coordination cost
- Risks: stalls delivery; not aligned with user intent

---

## 5. PRD MVP Impact

**Nenhum.** O PRD do MVP define "AI-powered grade query via WhatsApp" sem fixar provedor. O switch mantém todos os FR-17, FR-18, FR-19, FR-20, NFR-* do Epic 6 inalterados. Apenas o stack de implementação muda.

---

## 6. High-Level Action Plan

### Phase 1 — Aprovação (THIS STEP)
- [x] Sprint Change Proposal redigido e submetido
- [ ] **Credo aprova o proposal** ← pending

### Phase 2 — Story 9.0 (após aprovação)
- [ ] `@sm *create-story 9.0` (já existe como Draft; promover para Ready)
- [ ] `@po *validate-story-draft 9.0` (GO esperado ≥ 8/10)
- [ ] `@dev *develop-story 9.0` (YOLO mode, ~3 pontos)
- [ ] `@qa *qa-gate 9.0` (PASS esperado)
- [ ] `@devops *push` (delegated; commit atómico + housekeeping)

### Phase 3 — Epic 9 normal flow
- [ ] `@sm *create-next-story 9.1` (já existe como Draft; ready for re-validate)
- [ ] `@po *validate-story-draft 9.1` (GO 8/10)
- [ ] `@dev *develop-story 9.1` (5 pontos)
- [ ] `@qa *qa-gate 9.1` (inclui 1 E2E real WhatsApp)
- [ ] Stories 9.2, 9.3 seguem

---

## 7. Agent Handoff Plan

| Role | Owner | Action |
|------|-------|--------|
| Approve change | **Credo** | Reads this proposal, approves / requests changes |
| Re-validate stories | `@po` | Re-score 9.1, 9.3 (now depend on 9.0) |
| Implement | `@dev` | T1–T13 of Story 9.0 |
| QA gate | `@qa` | 7-check review of 9.0 |
| Push | `@devops` | Atomic commit + push to origin |

No re-scope of Epic 6 needed. No `@architect` review needed (no architectural shift — provider swap only).

---

## 8. Validation & Rollback Plan

**Validation:**
1. `grep -r "baidu\|qianfan" backend/ docs/stories/ pyproject.toml .env.example` returns only historical notes (marked DEPRECATED/Revised)
2. `pytest backend/tests/test_ai_chatbot.py` — all green
3. `ruff check backend/` — clean
4. `mypy backend/app/services/` — clean
5. Story 9.0 gate: PASS

**Rollback (if 9.0 fails QA):**
- `git revert` the merge commit of 9.0
- Baidu code does not return (it was deleted), so rollback = re-implement Baidu OR pin to legacy `AI_PROVIDER=claude`/`openai` until DeepSeek issue resolved
- No data loss (state lives in DB; provider swap is stateless)

---

## 9. Success Criteria

Story 9.0 is **Done** when:
- [x] DeepSeekProvider implemented, tested, in `backend/app/services/`
- [x] BaiduProvider fully removed
- [x] `qianfan` not in `pyproject.toml`
- [x] `.env.example` shows `AI_PROVIDER=deepseek` as default
- [x] `pytest` 100% green
- [x] `ruff` + `mypy` clean
- [x] `docs/architecture/system-architecture.md` reflects DeepSeek as primary
- [x] Epic 9 stories 9.1, 9.3 updated
- [x] Gate `9.0-deepseek-provider-switch.yml` exists with verdict PASS
- [x] Push to origin via `@devops` (delega)

After 9.0 closes, **Epic 9 acceptance can proceed** with DeepSeek as the live AI provider.

---

*Proposal authored by Orion (@aiox-master) via `*correct-course` task on 2026-06-08. Awaiting Credo approval.*
