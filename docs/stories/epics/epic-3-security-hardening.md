# Epic 3: Security Hardening

**Epic ID:** EPIC-3
**Status:** Done
**Created:** 2026-05-02
**Owner:** @pm (Morgan)

---

## Overview

Implementar medidas de segurança essenciais: autenticação, rate limiting, validação de input, sanitização de erros e validação de configuração startup.

## Business Context

O MVP atual possui **Security Score 3/10**:
- Sem autenticação → API completamente aberta
- Sem rate limiting → Abuse potencial
- Sem validação de input → Injection risk
- Erros expõem internals → Information disclosure
- Config não validada startup → Runtime failures

## Scope

### IN
- TD-001: Evolution API config startup validation
- TD-002: CSV input validation (schema validation)
- TD-003: Atomic file writes (data integrity)
- TD-004: Rate limiting middleware
- TD-005: Basic authentication/API key
- TD-006: Error message sanitization

### OUT
- Database migration
- OAuth/JWT implementation (basic auth sufficient for MVP)
- CORS restrictions (already enabled)
- Encryption at rest

## Success Criteria

| Criteria | Metric |
|----------|--------|
| Startup validation | App fails fast if config incomplete |
| Input validation | CSV schema validation rejects malformed |
| Rate limiting | 100 req/min per IP configured |
| Authentication | API key required for all /api/* routes |
| Error sanitization | No internal info in 5xx responses |
| Security Score | ≥ 7/10 |

## Dependencies

- **EPIC-2:** Quality foundation must be complete before security changes

## Stories

### Story 3.1: Config Startup Validation (TD-001)
- **Points:** 2
- **Owner:** @dev
- **Priority:** P1
- **Description:** Validate Evolution API config at app startup
- **File:** `docs/stories/3.1.config-startup-validation.md`

### Story 3.2: CSV Input Validation (TD-002)
- **Points:** 3
- **Owner:** @dev
- **Priority:** P1
- **Description:** Add Joi/Zod schema validation for CSV uploads
- **File:** `docs/stories/3.2.csv-input-validation.md`

### Story 3.3: Atomic File Writes (TD-003)
- **Points:** 2
- **Owner:** @dev
- **Priority:** P1
- **Description:** Implement atomic write pattern for JSON storage
- **File:** `docs/stories/3.3.atomic-file-writes.md`

### Story 3.4: Rate Limiting (TD-004)
- **Points:** 1
- **Owner:** @devops
- **Priority:** P1
- **Description:** Add express-rate-limit middleware
- **File:** `docs/stories/3.4.rate-limiting.md`

### Story 3.5: Basic Authentication (TD-005)
- **Points:** 4
- **Owner:** @devops
- **Priority:** P1
- **Description:** Implement API key authentication
- **File:** `docs/stories/3.5.basic-authentication.md`

### Story 3.6: Error Sanitization (TD-006)
- **Points:** 1
- **Owner:** @dev
- **Priority:** P1
- **Description:** Sanitize error messages in global handler
- **File:** `docs/stories/3.6.error-sanitization.md`

## Timeline

- **Sprint 2:** Week 2 (Stories 3.1-3.6)
- **Effort Total:** 13 points (~13h)

## Risks

| Risk | Mitigation |
|------|------------|
| Auth breaks existing frontend | Add API key to frontend config |
| Rate limit blocks legitimate use | Start conservative, monitor usage |
| Validation rejects valid CSVs | Test with real CSV samples |

---

*Epic created by @pm (Morgan) — 2026-05-02*