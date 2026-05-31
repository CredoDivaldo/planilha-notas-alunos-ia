# Auth Rollback Procedures

## Purpose

This document describes how to disable the new Python/FastAPI authentication
routes without touching Node.js legacy MVP endpoints, and how to handle users
created during the new auth foundation rollout.

---

## When to Roll Back

Roll back if:
- The new login endpoint causes data integrity issues.
- A regression in the audit log blocks professor operations.
- A session management bug causes widespread lockouts.

**Do NOT roll back** if only documentation or rate limiting (future story) is affected.

---

## Rollback Steps

### Step 1: Disable New Auth Routes (No Node Impact)

The new auth routes live under `/api/v1/auth/*` (Python/FastAPI).
The Node.js legacy routes live under different paths and are served by a separate process.

To disable new auth routes:

```bash
# Option A: Comment out the auth router include in main.py
# In backend/app/main.py, comment out:
#   app.include_router(auth_router, prefix="/api/v1/auth")

# Option B: Set an environment variable to skip auth route registration
# Add to .env:
DISABLE_AUTH_ROUTES=true
# And guard in main.py with: if not settings.disable_auth_routes: app.include_router(...)
```

Node.js endpoints are **not affected** by either option.

### Step 2: Preserve Created Users

Users created via the new foundation MUST NOT be deleted unless a local reset is explicitly chosen.

Reasons:
- Deletion would break audit log foreign keys (`audit_log.actor_user_id`).
- Grades and operations referencing these users would lose traceability.
- GDPR/compliance: retain records.

If a full local reset is explicitly chosen (dev/test environment only):

```bash
# WARNING: Destroys all data. Only for local development reset.
# Run Alembic downgrade to remove auth tables:
python -m alembic downgrade 20260528_0001

# Then re-run upgrade:
python -m alembic upgrade head
```

### Step 3: Invalidate All Sessions

If rolling back due to session bug, invalidate all active sessions:

```sql
-- Run via sqlite3 or equivalent
UPDATE user_sessions SET is_active = 0 WHERE is_active = 1;
```

This forces all users to re-authenticate when auth routes are re-enabled.

### Step 4: Verify Node Legacy Still Works

After disabling auth routes, verify:

```bash
# Node legacy health (adjust port as needed)
curl http://localhost:3000/api/health

# Python health (should still work — auth routes disabled, health is separate)
curl http://localhost:8000/api/v1/health
```

---

## Session Cookie Rollback

The `sid` cookie (`HttpOnly`, `SameSite=Lax`) is set only by the new Python auth routes.
Disabling those routes means no new cookies are issued. Existing cookies become harmless
(no route to validate them).

---

## Audit Log Preservation

The `audit_log` table and its new columns (`auth_event_type`, `failure_reason`) are
backward-compatible. Rows from before the migration have NULL values for these columns.
Rolling back auth routes does NOT require rolling back the Alembic migration unless a
full local reset is chosen.

---

## Related Files

- `backend/migrations/versions/20260531_0002_auth_and_role_foundation.py`
- `backend/app/auth/sessions.py`
- `backend/app/auth/middleware.py`
- `docs/framework/role-capability-matrix.md`
