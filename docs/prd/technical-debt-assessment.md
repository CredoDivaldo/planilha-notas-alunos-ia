# Technical Debt Assessment — Final Consolidation

> **Nota de reconciliação PO — 2026-05-28:** este assessment é histórico, datado de 2026-05-02. A ausência de scripts `test`, `lint` e `typecheck` já não reflecte o estado actual do repositório. O estado corrente é governado por `package.json`, Story 2.1, `docs/qa/gates/2.1-quality-scripts-baseline.yml` e `docs/reviews/po-master-validation-2026-05-28.md`. Itens ainda relevantes devem ser revalidados antes de serem promovidos a backlog activo.

**Project:** Planilha Notas Alunos IA
**Date:** 2026-05-02
**Assessment Type:** Complete Technical Audit (Brownfield Discovery Phase 8)
**Assessor:** @architect (Aria)

---

## Executive Summary

MVP local para importação de notas via CSV e envio de mensagens WhatsApp via Evolution API. Sistema funcional com **12 débitos técnicos** identificados, **8 débitos UX**, e **QA Gate: NEEDS WORK**.

| Métrica | Valor |
|---------|-------|
| Débitos Técnicos | 12 |
| Débitos UX | 8 |
| Críticos | 4 (TD-001, TD-002, UX-001, UX-002) |
| Altos | 7 |
| Médios | 9 |
| Baixos | 0 |
| QA Gate | NEEDS WORK |
| Esforço Total Estimado | ~40 horas |

---

## 1) Specialist Review Verdicts

| Specialist | Verdict | Key Findings |
|------------|---------|--------------|
| **@data-engineer** | SKIPPED | No database — JSON file storage |
| **@ux-design-expert** | APPROVED WITH CONCERNS | D10/D12/D15 elevated to P0; D11 should be P0/P1 boundary |
| **@qa** | NEEDS WORK | Missing test/lint/typecheck scripts; async error handling gaps |

---

## 2) Consolidated Debt Inventory

### P0 — Immediate (Blocks QA Approval)

#### TD-QG-01: Missing Quality Baseline Scripts
**Location:** `package.json`
**Issue:** No `npm run test`, `npm run lint`, `npm run typecheck` scripts
**Impact:** No automated quality gates; regressions undetected
**Effort:** 1h
**Recommendation:** Add Jest + ESLint + scripts

#### TD-QG-02: No Test Coverage for Critical Flow
**Location:** `tests/`
**Issue:** Only 1 test file; no coverage for upload→match→send flow
**Impact:** Hidden bugs; regression risk
**Effort:** 4h
**Recommendation:** Add tests per domain (students, grades, match, send)

#### TD-QG-03: Async Error Handling Inconsistent
**Location:** `src/routes/students.js`, `src/routes/grades.js`, `src/routes/match.js`
**Issue:** Async handlers without standardized error capture
**Impact:** Unhandled rejections; inconsistent HTTP responses
**Effort:** 2h
**Recommendation:** Apply `asyncHandler` wrapper uniformly

#### UX-001: No Error Handling UI
**Location:** `public/app.js`
**Issue:** `alert()` for errors — blocking, disruptive
**Impact:** Poor UX; no error recovery guidance
**Effort:** 3h
**Recommendation:** Inline error messages with toast notifications

#### UX-002: No Loading States
**Location:** `public/app.js` (all async ops)
**Issue:** No visual feedback during fetch operations
**Impact:** User uncertainty; perceived performance degradation
**Effort:** 2h
**Recommendation:** Add loading spinners; disable buttons during ops

---

### P1 — Short Term

#### TD-001: Config Evolution API No Startup Validation
**Location:** `src/services/evolution-client.js:3-14`
**Issue:** API credentials loaded without startup validation
**Impact:** Runtime failures if config incomplete
**Effort:** 2h
**Recommendation:** Add startup validation + config health endpoint

#### TD-002: No Input Validation on CSV Upload
**Location:** `src/routes/students.js:22-29`, `src/routes/grades.js`
**Issue:** No validation of CSV structure, field types, size limits
**Impact:** Malformed CSV causes runtime errors; potential injection
**Effort:** 3h
**Recommendation:** Add schema validation (Joi/Zod)

#### TD-003: File Storage Without Atomicity
**Location:** `src/services/storage.js:25-28`
**Issue:** `writeJson` overwrites files directly; no backup/rollback
**Impact:** Data loss on write failure; concurrent access issues
**Effort:** 2h
**Recommendation:** Implement atomic write (write to temp, rename)

#### TD-004: Missing Rate Limiting
**Location:** `src/app.js`
**Issue:** No rate limiting on API endpoints
**Impact:** API abuse potential; Evolution API quota exhaustion
**Effort:** 1h
**Recommendation:** Add `express-rate-limit` middleware

#### TD-005: Missing Authentication
**Location:** All routes
**Issue:** No auth mechanism; anyone can access API
**Impact:** Unauthorized access to student data; message spoofing
**Effort:** 4h
**Recommendation:** Add basic auth or JWT; minimum API key

#### TD-006: Error Messages Leak Internal Info
**Location:** `src/app.js:27-32`
**Issue:** Error handler exposes internal errors on 5xx
**Impact:** Information disclosure to attackers
**Effort:** 0.5h
**Recommendation:** Sanitize error messages; log internally only

#### UX-003: No Accessibility (a11y)
**Location:** `public/index.html`, `public/styles.css`
**Issue:** Missing ARIA labels, focus management, keyboard navigation
**Impact:** Excludes users with disabilities; WCAG AA non-compliance
**Effort:** 4h
**Recommendation:** Add ARIA attributes, focus indicators, semantic structure

#### UX-004: No Form Validation Feedback
**Location:** `public/index.html` forms, `public/app.js` handlers
**Issue:** No client-side validation before submit
**Impact:** Server rejected uploads; wasted requests
**Effort:** 2h
**Recommendation:** Validate file type/size before upload

#### UX-005: QR Code Polling Missing
**Location:** `public/app.js:connectEvolution()`
**Issue:** User must manually click to check connection state
**Impact:** Confusing UX; no auto-feedback when connected
**Effort:** 2h
**Recommendation:** Implement polling or SSE for connection state

---

### P2 — Medium Term

#### TD-007: Missing Request Logging
**Location:** `src/app.js`
**Issue:** No request logging middleware
**Impact:** Difficult debugging; no audit trail
**Effort:** 1h
**Recommendation:** Add `morgan` or custom logger

#### TD-008: Frontend Single File Concentration
**Location:** `public/app.js` (198 lines)
**Issue:** All workflow logic in single file
**Impact:** Maintenance difficult; scalability limit
**Effort:** 2h
**Recommendation:** Modularize by step components

#### TD-009: JSON Files Not Suitable for Production
**Location:** `data/*.json`
**Issue:** JSON files not suitable for concurrent access, querying
**Impact:** Scalability limit; data integrity risks
**Effort:** 4h (if migration)
**Recommendation:** Evaluate SQLite or Supabase for production

#### UX-006: No Design System
**Location:** `public/styles.css`
**Issue:** Hardcoded colors, fonts, spacing — no tokens
**Impact:** Maintenance burden; visual inconsistency
**Effort:** 2h
**Recommendation:** Define CSS variables, reusable classes

#### UX-007: No Responsive Design
**Location:** `public/styles.css`, `public/index.html`
**Issue:** Desktop-only layout; no mobile/tablet breakpoints
**Impact:** Poor experience on mobile devices
**Effort:** 2h
**Recommendation:** Add media queries, responsive grid

#### UX-008: No User Confirmation Dialogs
**Location:** `public/app.js:sendBulkMessages()`
**Issue:** Send action has no confirmation — irreversible
**Impact:** Risk of accidental message sends
**Effort:** 1h
**Recommendation:** Add confirmation modal before bulk send

---

## 3) Execution Roadmap

### Week 1: P0 Quality Baseline
```
Day 1-2: QG-01 (quality scripts) + QG-03 (async error handling)
Day 3-4: QG-02 (test coverage) + UX-001 (error UI) + UX-002 (loading)
Day 5: Integration testing + QA re-validation
```

### Week 2: P1 Security & UX
```
Day 1-2: TD-001 (config validation) + TD-002 (CSV validation) + TD-006 (error sanitization)
Day 3-4: TD-003 (atomic writes) + TD-004 (rate limiting) + TD-005 (auth)
Day 5: UX-003 (a11y) + UX-004 (form validation) + UX-005 (polling)
```

### Week 3-4: P2 Refinement
```
Week 3: TD-007 (logging) + TD-008 (frontend modularize) + UX-006 (design system)
Week 4: UX-007 (responsive) + UX-008 (confirmation) + TD-009 evaluation
```

---

## 4) QA Gate Criteria for APPROVED

1. `npm run test`, `npm run lint`, `npm run typecheck` execute without failures
2. All critical flow scenarios have automated tests passing
3. Async routes use standardized error handling with consistent response contract
4. Evidence documented in `docs/reviews/evidence/` with date/commit reference
5. QA re-execution confirms no blockers from items 1-3

---

## 5) UX Gate Criteria for APPROVED Without Reservations

- [ ] Gating complete by step (locked/active/completed/error)
- [ ] Send confirmation without `alert()`, with accessible modal and managed focus
- [ ] Associated `labels` + functional `aria-live` in uploads/processing/send
- [ ] Semantic feedback unified in critical flow
- [ ] MatchDataView with functional mobile behavior for quick decision
- [ ] Preservation of last valid state when regeneration fails

---

## 6) Metrics Summary

| Category | Count | Critical | High | Medium |
|----------|-------|----------|------|--------|
| Technical Debt | 12 | 2 | 4 | 6 |
| UX Debt | 8 | 2 | 3 | 3 |
| QA Findings | 3 | 3 | 0 | 0 |
| **Total** | **23** | **7** | **7** | **9** |

---

## 7) Next Steps (Workflow)

- **FASE 9:** @analyst → `docs/reports/TECHNICAL-DEBT-REPORT.md` (executive summary)
- **FASE 10:** @pm → Create Epic + Stories for development

---

*Assessment finalized by Aria (@architect) — 2026-05-02*
*Specialist reviews: @ux-design-expert (APPROVED WITH CONCERNS), @qa (NEEDS WORK)*
