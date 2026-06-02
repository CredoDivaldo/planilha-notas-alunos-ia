# Epic 2: Quality Foundation

**Epic ID:** EPIC-2
**Status:** Draft
**Created:** 2026-05-02
**Owner:** @pm (Morgan)

---

## Overview

Estabelecer baseline de qualidade automatizada (testes, lint, typecheck) e padronização de tratamento de erro em rotas assíncronas críticas. Este epic é **blocking** para qualquer evolução futura do sistema.

## Business Context

O MVP atual carece de:
- Scripts npm de qualidade (`test`, `lint`, `typecheck`)
- Cobertura de testes para o fluxo crítico upload→match→send
- Tratamento de erro consistente em rotas assíncronas

Sem estas foundations, qualquer mudança introduz risco de regressão silenciosa.

## Scope

### IN
- Implementação de scripts npm (QG-01)
- Suíte de testes automatizados (QG-02)
- Padronização async error handling (QG-03)
- UX error handling básico (UX-001 loading portion)

### OUT
- Autenticação/Authorization (Epic 3)
- Design system (Epic 4)
- Database migration (future evaluation)
- Rate limiting (Epic 3)

## Success Criteria

| Criteria | Metric |
|----------|--------|
| Scripts funcionais | `npm run test/lint/typecheck` executam sem falha |
| Test coverage | 100% dos cenários críticos cobertos |
| Error handling | Todas rotas async com `asyncHandler` |
| QA Gate | APPROVED |

## Dependencies

- None (foundation epic)

## Stories

### Story 2.1: Quality Scripts Baseline (QG-01)
- **Points:** 2
- **Owner:** @dev
- **Priority:** P0
- **Description:** Add `npm run test`, `npm run lint`, `npm run typecheck` scripts
- **File:** `docs/stories/2.1.quality-scripts-baseline.md`

### Story 2.2: Critical Flow Tests (QG-02)
- **Points:** 5
- **Owner:** @qa
- **Priority:** P0
- **Description:** Implement test suite for upload→match→send flow
- **File:** `docs/stories/2.2.critical-flow-tests.md`

### Story 2.3: Async Error Standardization (QG-03)
- **Points:** 3
- **Owner:** @dev
- **Priority:** P0
- **Description:** Apply `asyncHandler` wrapper to all async routes
- **File:** `docs/stories/2.3.async-error-standardization.md`

### Story 2.4: Error UI Foundation (UX-001 partial)
- **Points:** 3
- **Owner:** @dev + @ux-design-expert
- **Priority:** P0
- **Description:** Replace `alert()` with toast notifications
- **File:** `docs/stories/2.4.error-ui-foundation.md`

### Story 2.5: Loading States (UX-002)
- **Points:** 2
- **Owner:** @ux-design-expert
- **Priority:** P0
- **Description:** Add loading spinners and button states during async ops
- **File:** `docs/stories/2.5.loading-states.md`

## Timeline

- **Sprint 1:** Week 1 (Stories 2.1-2.5)
- **Effort Total:** 15 points (~15h)

## Risks

| Risk | Mitigation |
|------|------------|
| Jest configuration complexity | Use minimal config, follow existing patterns |
| Test flakiness with Evolution API | Mock external API calls |
| Frontend changes break existing behavior | Incremental implementation with tests |

---

*Epic created by @pm (Morgan) — 2026-05-02*