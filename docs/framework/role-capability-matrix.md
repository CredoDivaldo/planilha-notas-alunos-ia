# Role Capability Matrix

## Overview

This document defines the access boundaries for each role in the academic platform.
It is the authoritative reference for backend authorization decisions.

Roles are stored in `users.role` (string column, values: `professor`, `student`, `delegate`, `admin_local`).

---

## Roles

| Role | Identity Type | Scope |
|------|--------------|-------|
| `professor` | Individual staff account | Own academic contexts (turma + subject + semester) |
| `student` | Student account linked to `students.user_id` | Own published data only |
| `delegate` | Student with additional operational assignment | Specific turma/context — NOT global |
| `admin_local` | Bootstrap-only local admin | Full access — for initial setup only; disable after setup |

---

## Capability Matrix

| Action | professor | student | delegate | admin_local | Notes |
|--------|-----------|---------|----------|-------------|-------|
| View own published grade snapshots | — | ALLOW | ALLOW | ALLOW | Student sees own; delegate sees own as student |
| View unpublished/internal grade entries | ALLOW (own contexts) | BLOCK | BLOCK | ALLOW | |
| Create/edit grade entries | ALLOW (own contexts) | BLOCK | BLOCK | ALLOW | |
| Delete grade entries | ALLOW (own contexts) | BLOCK | BLOCK | ALLOW | |
| Publish grade snapshots | ALLOW (own contexts) | BLOCK | REQUIRES_PROFESSOR_VALIDATION | ALLOW | Delegate triggers, professor approves |
| Create assessment definitions | ALLOW (own contexts) | BLOCK | BLOCK | ALLOW | |
| Manage class groups | ALLOW (own assignments) | BLOCK | BLOCK | ALLOW | |
| Assign delegate to context | ALLOW (own contexts) | BLOCK | BLOCK | ALLOW | |
| Approve delegate assignment | ALLOW (own contexts) | BLOCK | BLOCK | ALLOW | |
| View delegate assignment state | ALLOW | BLOCK | ALLOW (own) | ALLOW | |
| Broadcast grade notifications | ALLOW (own contexts) | BLOCK | REQUIRES_PROFESSOR_VALIDATION | ALLOW | |
| Manage calendar events | ALLOW (own contexts) | BLOCK | REQUIRES_PROFESSOR_VALIDATION | ALLOW | |
| View own calendar events | — | ALLOW (published) | ALLOW (published) | ALLOW | |
| Change own password | ALLOW | ALLOW | ALLOW | ALLOW | Must change on first login |
| Manage other users | BLOCK | BLOCK | BLOCK | ALLOW | admin_local only |
| Trigger credential delivery | ALLOW (own contexts) | BLOCK | BLOCK | ALLOW | |

---

## Delegate Scoping Rules

Delegates are students with a **scoped assignment** in `delegate_assignments`:

1. A delegate assignment links a `user_id` (student) to a `context_type` + `context_id`
   (e.g., `class_group:42`).
2. The assignment has a `state`: `pending` → `approved` → `rejected`.
3. `requires_professor_validation = true` (default, non-negotiable for sensitive actions).
4. Delegate capabilities only activate when `state = approved`.
5. Delegate rights are **not cumulative** — each context must be individually approved.
6. A delegate can never exceed the permissions of a `professor` in the same context.

---

## Sensitive Actions (Requires Professor Validation)

Actions where delegate action is submitted but professor must approve before execution:

| Action | Validation Mechanism |
|--------|---------------------|
| Publish grade snapshots | `delegate_assignments.state` workflow + explicit professor confirmation endpoint |
| Broadcast notifications | Same as above |
| Calendar event publish | Same as above |

These are represented as `REQUIRES_PROFESSOR_VALIDATION` in the matrix above.

---

## First-Access Password Change

All new accounts have `users.must_change_password = true`.

A user with `must_change_password = true` MUST be redirected to password change before
accessing any other endpoint. This is enforced at the middleware/dependency level.

---

## admin_local Bootstrap Role

`admin_local` is intended for:
- Initial system setup
- Creating the first professor accounts
- Emergency recovery

It should be **disabled** (set `is_active = false` or delete) after initial setup.
Never use `admin_local` as a permanent operational role.

---

## Related Files

- `backend/app/auth/password.py` — Argon2id hashing
- `backend/app/auth/sessions.py` — Session management
- `backend/app/auth/middleware.py` — Auth observability
- `backend/migrations/versions/20260531_0002_auth_and_role_foundation.py` — Schema
- `docs/framework/auth-rollback.md` — Rollback instructions
