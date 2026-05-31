# API Documentation Handoff

**Status:** placeholder controlado para Epic 5.  
**Fonte actual:** `docs/architecture.md`, secção "Estratégia de API e Integração".

## Decisão

O backend Python nasce em `backend/app/main.py`, mantém endpoints novos sob `/api/v1` e disponibiliza OpenAPI runtime gerado pelo FastAPI.

Execução local mínima:

```bash
python3 -m uvicorn backend.app.main:app --reload --port 8000
```

Verificações de contrato em runtime:

- Health: `GET /api/v1/health`
- OpenAPI: `GET /openapi.json`

Quando os primeiros endpoints estabilizarem, o contrato deve ser exportado para `docs/api/openapi.json` ou artefacto equivalente e referenciado pelas stories afectadas.

Exemplo de exportação local:

```bash
python3 - <<'PY'
import json
from pathlib import Path
from backend.app.main import app

Path("docs/api/openapi.json").write_text(
    json.dumps(app.openapi(), ensure_ascii=False, indent=2),
    encoding="utf-8",
)
PY
```

## Rate Limiting Requirements

### Authentication Endpoints

Rate limiting MUST be applied to the following endpoints (implementation in a future story):

| Endpoint | Limit | Window | Action on Breach |
|----------|-------|--------|-----------------|
| `POST /api/v1/auth/login` | 10 attempts | 15 minutes per IP | 429 Too Many Requests + audit log |
| `POST /api/v1/auth/password-change` | 5 attempts | 10 minutes per user | 429 + audit log |
| Any auth endpoint for a single username | 5 attempts | 10 minutes | Temporary account lock + audit |

### Implementation Notes (Deferred to future story)

- Use a sliding-window counter stored in SQLite (no Redis required for local-only deployment).
- Failure reason in audit log: `failure_reason = "rate_limited"` (see `backend/app/auth/middleware.py`).
- Rate limit state is per-IP for login; per-user for password operations.
- Lock duration: 15 minutes (exponential back-off is out of scope for MVP).
- No CAPTCHA in MVP — lockout is sufficient for a local academic platform.

---

## Fora de Escopo Nesta Fase

- Contrato manual completo antes da existência do backend.
- CI/CD remoto para publicação de OpenAPI.
- Gateway cloud, canary, blue/green ou ambiente de produção remoto.

## Critério Mínimo por Story

Qualquer story que crie endpoint Python deve:
- manter namespace `/api/v1`;
- preservar endpoints Node legados durante a transição;
- actualizar ou referenciar OpenAPI gerado;
- incluir teste ou verificação manual do contrato;
- não expor segredos, palavras-passe, payloads internos de auditoria ou notas não publicadas.
