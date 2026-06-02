# TECHNICAL DEBT REPORT — Executive Summary

> **Nota de reconciliação PO — 2026-05-28:** este relatório é histórico, datado de 2026-05-02. Os blockers de ausência de scripts/testes foram endereçados posteriormente pela Story 2.1 e pela baseline actual de `package.json`. Para desenvolvimento do Epic 5, usar `docs/architecture.md`, `docs/stories/epics/epic-5-academic-platform-foundation.md`, as stories 5.1-5.5 e o gate `docs/qa/gates/2.1-quality-scripts-baseline.yml` como fontes actuais. Débitos remanescentes de segurança, UX, observabilidade e persistência continuam úteis como contexto, mas devem ser revalidados antes de execução.

**Project:** Planilha Notas Alunos IA
**Date:** 2026-05-02
**Report Type:** Brownfield Discovery Executive Output (Phase 9)
**Author:** Alex (@analyst)

---

## Resumo Executivo

O projecto **Planilha Notas Alunos IA** é um MVP funcional que automatiza o envio de notas de alunos via WhatsApp através da Evolution API. O sistema está **operacionalmente pronto** mas carece de **fundamentos de qualidade** necessários para sustentar evolução segura.

**Status do Quality Gate:** NEEDS WORK — 3 blockers críticos identificados.

---

## Situação Actual

### O que funciona
- Upload de CSV de estudantes e notas
- Matching automático entre dados
- Integração com Evolution API (WhatsApp)
- Envio em massa com modo dry-run (simulação)
- QR code para conexão WhatsApp

### O que precisa atenção urgente
- **Zero testes automatizados** para o fluxo crítico
- **Zero scripts de qualidade** (test, lint, typecheck)
- **Tratamento de erro inconsistente** nas rotas assíncronas
- **Interface sem feedback de loading** durante operações
- **Erros apresentados via alert()** — UX pobre

---

## Débitos por Categoria

| Categoria | Débitos | Críticos | Esforço |
|-----------|---------|----------|---------|
| **Qualidade & Testes** | 3 | 3 | 7h |
| **Segurança** | 5 | 2 | 10.5h |
| **Arquitetura** | 4 | 0 | 9h |
| **UX/Acessibilidade** | 8 | 2 | 16h |
| **Observabilidade** | 3 | 0 | 4h |
| **TOTAL** | **23** | **7** | **~40h** |

---

## Riscos Identificados

### Risco 1: Regressões Silenciosas (CRÍTICO)
- Sem testes automatizados, qualquer mudança pode introduzir bugs
- **Impacto:** Falhas em produção sem detecção prévia
- **Mitigação:** Implementar baseline de testes (QG-02)

### Risco 2: Falha de Configuração em Produção (CRÍTICO)
- Evolution API config validada apenas em runtime
- **Impacto:** Sistema falha ao iniciar se .env incompleto
- **Mitigação:** Startup validation (TD-001)

### Risco 3: Erro Operacional por UX Insuficiente (CRÍTICO)
- Fluxo não guiado por pré-condições
- Utilizador pode disparar mensagens sem match válido
- **Impacto:** Envio de mensagens erradas, risco reputacional
- **Mitigação:** State gating (UX-001, UX-002)

### Risco 4: Vulnerabilidade de Segurança (ALTO)
- Sem autenticação, rate limiting, ou validação de input
- **Impacto:** API aberta a abuso, injection potencial
- **Mitigação:** Auth + rate limit + input validation (TD-002, TD-004, TD-005)

---

## Roadmap de Remediação

### Sprint 1 (Week 1): Foundation
**Objetivo:** Estabelecer baseline de qualidade

| Task | Effort | Owner |
|------|--------|-------|
| QG-01: Scripts npm (test/lint/typecheck) | 1h | @dev |
| QG-03: Padronização async error handling | 2h | @dev |
| QG-02: Testes críticos (4 domínios) | 4h | @qa |
| UX-001: Error UI (toast notifications) | 3h | @ux-design-expert |
| UX-002: Loading states | 2h | @ux-design-expert |

**Total Sprint 1:** ~12h
**Resultado esperado:** QA Gate → APPROVED

### Sprint 2 (Week 2): Security & UX Core
**Objetivo:** Mitigar riscos de segurança e UX críticos

| Task | Effort | Owner |
|------|--------|-------|
| TD-001: Config startup validation | 2h | @dev |
| TD-002: CSV input validation | 3h | @dev |
| TD-006: Error sanitization | 0.5h | @dev |
| TD-003: Atomic file writes | 2h | @dev |
| TD-004: Rate limiting | 1h | @devops |
| TD-005: Basic authentication | 4h | @devops |
| UX-003: Accessibility basics | 4h | @ux-design-expert |
| UX-004: Form validation feedback | 2h | @ux-design-expert |
| UX-005: QR polling | 2h | @dev |

**Total Sprint 2:** ~18.5h
**Resultado esperado:** Security Score → 7/10, UX Gate → APPROVED

### Sprint 3 (Week 3-4): Refinement
**Objetivo:** Melhorar manutenibilidade e experiência

| Task | Effort | Owner |
|------|--------|-------|
| TD-007: Request logging | 1h | @devops |
| TD-008: Frontend modularization | 2h | @dev |
| UX-006: Design system tokens | 2h | @ux-design-expert |
| UX-007: Responsive design | 2h | @ux-design-expert |
| UX-008: Confirmation dialogs | 1h | @ux-design-expert |
| TD-009: DB evaluation | 4h | @architect |

**Total Sprint 3:** ~12h
**Resultado esperado:** Tech Debt Score → C

---

## Investment Analysis

### Cost of Remediation
- **Total effort:** ~40 horas
- **Equivalent:** 1 semana de desenvolvimento dedicado
- **Or:** 2-3 sprints paralelos com equipa existente

### Cost of Inaction
- **Regression risk:** Cada deploy sem testes = risco de falha
- **Security breach:** API aberta = potencial abuso/dados expostos
- **Operational error:** UX insuficiente = envio errado de mensagens
- **Estimated cost:** Significantly higher than remediation (incident response, reputation damage)

### ROI
- **Remediation:** 40h investidas → sistema production-ready
- **ROI timeline:** Payback em primeiro incident evitado

---

## Recommendations to Stakeholders

### Immediate (This Week)
1. **Prioritize QG-01/QG-02/QG-03** — Blocks all future development
2. **Allocate dedicated time** — 12h for Sprint 1 foundation
3. **Assign owners** — @dev for backend, @ux-design-expert for frontend, @qa for tests

### Short Term (Next 2 Weeks)
4. **Security hardening** — Authentication, rate limiting, input validation
5. **UX gating** — Prevent operational errors before they happen
6. **Accessibility compliance** — WCAG AA minimum

### Medium Term (Month)
7. **Evaluate database migration** — JSON files limit scalability
8. **Design system** — Reduce long-term maintenance cost
9. **Monitoring/Observability** — Production visibility

---

## Quality Gate Status

| Gate | Status | Blockers |
|------|--------|----------|
| **QA Gate** | NEEDS WORK | 3 critical (QG-01, QG-02, QG-03) |
| **UX Gate** | APPROVED WITH CONCERNS | Implementation pending |
| **Security Gate** | FAIL | 5 issues (auth, rate limit, validation, error leak, config) |
| **Overall** | **NOT READY FOR PRODUCTION** | Foundation required |

---

## Conclusion

O MVP demonstra que a solução é **tecnicamente viável** e **operacionalmente útil**. Contudo, a falta de baseline de qualidade, segurança e UX foundations cria **riscos significativos** para adopção em produção.

**Recommendation:** Executar Sprint 1 (12h) imediatamente para estabelecer foundation, depois prosseguir com Sprint 2 para security/UX. O investimento de ~40h transforma o MVP em sistema production-ready com confiança de evolução segura.

---

*Report prepared by Alex (@analyst) — 2026-05-02*
*Full assessment: `docs/prd/technical-debt-assessment.md`*
