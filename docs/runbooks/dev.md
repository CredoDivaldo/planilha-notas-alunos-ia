# Local Dev Runbook

> Story 8.3 — unified `npm run dev` flow.

## Quick start

```bash
npm run dev
```

This single command starts **both** servers in a single terminal:

| Service   | Port | URL                       | Color in terminal |
|-----------|------|---------------------------|-------------------|
| FastAPI   | 8000 | http://localhost:8000     | blue              |
| Vite      | 5173 | http://localhost:5173     | green             |

Open **http://localhost:5173** in your browser. Use this for all frontend work — Vite proxies all backend calls to FastAPI.

## How it works

`npm run dev` runs [`concurrently`](https://www.npmjs.com/package/concurrently) which spawns:

1. `npm run dev --prefix backend` → `cd .. && .venv/bin/python -m uvicorn backend.app.main:app --reload --port 8000`
2. `npm run dev --prefix client` → `vite`

The Vite dev server proxies the following path prefixes to FastAPI (see `client/vite.config.ts`):

- `/api`
- `/whatsapp`
- `/students`
- `/grades`
- `/broadcast`

Single regex match: `'^/(api|whatsapp|students|grades|broadcast)'`.

## Verification (AC checks)

```bash
# AC1: both servers up
npm run dev
# → see [backend] Uvicorn running on http://127.0.0.1:8000
# → see [client] VITE … ready … Local: http://localhost:5173/

# AC2: Vite proxies to FastAPI
curl -i http://localhost:5173/api/v1/health
# → HTTP/1.1 200 OK
# → {"status":"ok",…}

# AC3: same for WhatsApp
curl -i http://localhost:5173/api/v1/whatsapp/status
# → HTTP/1.1 200 OK
# → {"connected":false,"instance_name":"whatsapp-instance","simulated":true}
```

## Running services individually

If you need to run only one (e.g. backend-only test work):

```bash
npm run dev:backend   # FastAPI on :8000
npm run dev:client    # Vite on :5173
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: No module named 'backend'` | backend script must run from project root | The script `cd ..` before invoking uvicorn — don't run `npm run dev --prefix backend` from inside `backend/` |
| `[client] Port 5173 is in use` | Another Vite is still alive | `pkill -f vite` |
| `[backend] Port 8000 is in use` | Stale uvicorn | `pkill -f "uvicorn backend.app.main"` |
| One process dies, other logs show exit code | Concurrently surfaces the failure with `[backend] exited with code N` — that's expected | Restart `npm run dev` |
| Vite can't proxy to FastAPI (502) | Backend not yet started | Wait ~2s after launch, or check backend log for errors |

## Why one command?

Before Story 8.3, devs had to:

1. Open terminal A → activate venv → `uvicorn backend.app.main:app --reload`
2. Open terminal B → `cd client && npm run dev`
3. Manually keep them in sync on the correct ports

After: one terminal, one command, both processes stream interleaved with color labels (`[backend]` blue, `[client]` green) so logs are easy to read.
