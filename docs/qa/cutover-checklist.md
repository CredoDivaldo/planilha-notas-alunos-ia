# Cutover Verification Checklist — Story 8.6

**Purpose:** Human-runnable, copy-pasteable verification that the legacy Express
tree is fully cut over to FastAPI + React. Each block is one assertion you can
paste into a terminal with the dev stack running (`npm run dev`).

**How to run:**

```bash
# Terminal 1 — boot the full stack
cd /Users/user/10_Projects/Planilha\ notas\ alunos\ IA
npm run dev
# Wait for both "VITE ready" and "Uvicorn running on http://0.0.0.0:8000"
```

Then run each curl below in a second terminal. Each block is **independent** and
can be run in any order. The 6 happy-path blocks walk the user flow, the 3
regression blocks prove the legacy Express surface is gone.

**Fixtures used:**

- `legacy/fixtures/students_teste.csv`
- `legacy/fixtures/notas_teste.csv`

---

## HP-1 — Professor login (mock auth fallback)

Expected: HTTP 200, response JSON has `role: "professor"`. The local SPA falls
back to the AuthContext mock when `/auth/login` is unreachable, so this block
also doubles as a smoke test of `/login` route.

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email_or_student_number":"professor@example.com","password":"demo","role":"professor"}' \
  | head -20
```

---

## HP-2 — Upload students fixture

Expected: HTTP 200, JSON `{"inserted": N, "skipped": M, "errors": []}` where
N matches the row count of `students_teste.csv` (2 rows in the default fixture).

```bash
curl -i -X POST http://localhost:8000/api/v1/students/upload \
  -H 'Accept: application/json' \
  -F "file=@legacy/fixtures/students_teste.csv"
```

---

## HP-3 — Upload grades fixture

Expected: HTTP 200, JSON `{"inserted": N, "skipped": M, "errors": []}` where
N matches the row count of `notas_teste.csv` (2 rows in the default fixture).

```bash
curl -i -X POST http://localhost:8000/api/v1/grades/upload \
  -H 'Accept: application/json' \
  -F "file=@legacy/fixtures/notas_teste.csv"
```

---

## HP-4 — Trigger match (compute matched / unmatched / invalid)

Expected: HTTP 200, JSON containing `matched`, `unmatched`, `invalid_phones`,
`items`. With the bundled fixtures you should see `matched == 2` and the rest
`0`.

```bash
curl -i -X POST http://localhost:8000/api/v1/grades/match \
  -H 'Content-Type: application/json' \
  -d '{"context_id": "default"}' | head -40
```

---

## HP-5 — WhatsApp connection status (badge contract)

Expected: HTTP 200, JSON `{"connected": bool, "instance_name": str,
"simulated": bool}`. The dashboard badge uses this contract to render
"connected" / "disconnected" / "simulated".

```bash
curl -i http://localhost:8000/api/v1/whatsapp/status
```

---

## HP-6 — Broadcast dry-run

Expected: HTTP 200, JSON containing a `dry_run: true` flag and a preview list
of messages. **No real WhatsApp messages should be sent.**

```bash
curl -i -X POST http://localhost:8000/api/v1/broadcast/dry-run \
  -H 'Content-Type: application/json' \
  -d '{"context_id": "default", "template": "Olá {nome}, sua nota é {nota}."}' | head -40
```

---

## REG-1 — Legacy Express `/api/students/upload` must be GONE

Expected: HTTP **404** (NOT 200, NOT 500). The Express tree was removed in
Story 8.5; this assertion proves the cutover is complete and that the old
path can no longer serve a request.

```bash
curl -i http://localhost:8000/api/students/upload
# Expect: HTTP/1.1 404 Not Found
```

---

## REG-2 — New FastAPI `/api/v1/health` works

Expected: HTTP 200, JSON `{"status": "ok", "service": str, "api_prefix":
"/api/v1", "database": {...}}`.

```bash
curl -i http://localhost:8000/api/v1/health
# Expect: HTTP/1.1 200 OK
#         "status":"ok"
#         "api_prefix":"/api/v1"
```

---

## REG-3 — New FastAPI `/api/v1/whatsapp/status` works

Expected: HTTP 200, JSON `{"connected": bool, "instance_name": str,
"simulated": bool}`. (Identical contract to HP-5, but checked standalone as a
regression of the cutover routing layer.)

```bash
curl -i http://localhost:8000/api/v1/whatsapp/status
# Expect: HTTP/1.1 200 OK
#         body contains "connected" boolean
```

---

## Summary

| # | Block | Expected status | Pass criterion |
|---|-------|-----------------|----------------|
| HP-1 | Professor login | 200 (or mock fallback) | Login form visible at `/login` |
| HP-2 | Students upload | 200 | `inserted >= 1` |
| HP-3 | Grades upload | 200 | `inserted >= 1` |
| HP-4 | Match | 200 | `matched >= 1` |
| HP-5 | WhatsApp status | 200 | `connected` is boolean |
| HP-6 | Broadcast dry-run | 200 | `dry_run: true` |
| REG-1 | Old Express path | **404** | Not 200, not 500 |
| REG-2 | New health | 200 | `status: "ok"` |
| REG-3 | New WhatsApp status | 200 | `connected` is boolean |

**Cutover complete when all 9 rows are green.**
