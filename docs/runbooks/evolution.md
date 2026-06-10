# Evolution API — Production Runbook

> Story 9.3 — Epic 9 Real-Evolution Acceptance Run.
> **Last verified against commit:** `a4ad3fe` (Story 9.2 — 2026-06-09)

---

## Table of Contents

1. [TL;DR / Quick Reference](#1-tldr--quick-reference)
2. [Bring-up — Docker Compose + Env Vars](#2-bring-up--docker-compose--env-vars)
3. [Pairing WhatsApp](#3-pairing-whatsapp)
4. [Key Rotation](#4-key-rotation)
5. [Failure Modes](#5-failure-modes)
6. [Log Locations & Grep Recipes](#6-log-locations--grep-recipes)
7. [Backup / Restore Postgres](#7-backup--restore-postgres)
8. [Sanitisation Contract](#8-sanitisation-contract)
9. [Rate Limiting](#9-rate-limiting)
10. [Architecture Reference](#10-architecture-reference)
11. [Change Log](#11-change-log)

---

## 1. TL;DR / Quick Reference

Five commands that cover 90 % of operator actions:

```bash
# 1. Start the full Evolution stack
docker compose -f docker-compose.evolution.yml up -d

# 2. Check all three containers are healthy
docker compose -f docker-compose.evolution.yml ps

# 3. Tail Evolution API logs (ctrl-C to stop)
docker logs evolution_api -f

# 4. Backup the database right now
docker exec evolution_postgres pg_dump -U user evolution > backup-$(date +%F).sql

# 5. Restart only the Evolution API container (after .env change)
docker compose -f docker-compose.evolution.yml restart evolution_api
```

---

## 2. Bring-up — Docker Compose + Env Vars

### 2.1 Stack Overview

The `docker-compose.evolution.yml` file in the project root defines three services:

| Service | Container Name | Image | Port(s) | Volume |
|---|---|---|---|---|
| Evolution API | `evolution_api` | `evoapicloud/evolution-api:latest` | 8080 → 8080 | `evolution_instances` |
| Redis | `evolution_redis` | `redis:latest` | — (internal) | `evolution_redis` |
| Postgres | `evolution_postgres` | `postgres:15` | — (internal) | `evolution_postgres` |

All data is persisted in named Docker volumes — they survive container restarts and `down` commands unless explicitly removed with `-v`.

### 2.2 Starting the Stack

```bash
# Start in detached mode (works on macOS and Linux)
docker compose -f docker-compose.evolution.yml up -d

# Verify all containers are running
docker compose -f docker-compose.evolution.yml ps
```

Expected output:

```
NAME                   STATUS
evolution_api          running
evolution_redis        running
evolution_postgres     running
```

### 2.3 Stopping and Removing

```bash
# Stop (volumes preserved)
docker compose -f docker-compose.evolution.yml down

# Stop AND remove volumes (full reset — WARNING: destroys all data)
docker compose -f docker-compose.evolution.yml down -v
```

### 2.4 Required Environment Variables

The Evolution API container reads from `.env.evolution` (via `env_file:` in the compose file). The FastAPI backend reads from the root `.env`. Both files must exist before starting.

#### Root `.env` — FastAPI variables consumed by Evolution integration

| Variable | Example Value | Description |
|---|---|---|
| `EVOLUTION_BASE_URL` | `http://localhost:8080` | Base URL of the Evolution API container |
| `EVOLUTION_API_KEY` | `<your-evolution-api-key>` | Master API key for Evolution (set in Manager UI) |
| `EVOLUTION_INSTANCE` | `turma-c` | WhatsApp instance name to use for sending |
| `CHATBOT_WEBHOOK_TOKEN` | `<your-webhook-token>` | Bearer token that Evolution sends to FastAPI |
| `DEEPSEEK_API_KEY` | `<your-deepseek-api-key>` | DeepSeek AI provider key |
| `AI_PROVIDER` | `deepseek` | Must be `deepseek` for production |
| `AI_MODEL` | `deepseek-chat` | DeepSeek model identifier |

> **Note:** The code also accepts `EVOLUTION_API_URL` as an alias for `EVOLUTION_BASE_URL`
> (see `backend/app/services/evolution_api_client.py` line 37 for the env var lookup order).

#### Minimal `.env.evolution` — passed directly to Evolution API container

```dotenv
SERVER_URL=http://localhost:8080
AUTHENTICATION_API_KEY=<your-evolution-api-key>
DATABASE_PROVIDER=postgresql
DATABASE_CONNECTION_URI=postgresql://user:pass@evolution_postgres:5432/evolution
CACHE_REDIS_URI=redis://evolution_redis:6379/0
```

> **CRITICAL:** Never paste real credentials into documentation. Use `<your-key-here>` as a placeholder when sharing or committing examples.

### 2.5 First-Time Setup Checklist

- [ ] Create `.env.evolution` with the variables above
- [ ] Ensure `.env` has all 7 FastAPI variables
- [ ] Run `docker compose -f docker-compose.evolution.yml up -d`
- [ ] Confirm `docker compose -f docker-compose.evolution.yml ps` shows all 3 containers running
- [ ] Open `http://localhost:8080` — should return the Evolution API JSON welcome response

---

## 3. Pairing WhatsApp

### 3.1 Step-by-Step

**Step 1 — Start the stack (if not already running)**

```bash
docker compose -f docker-compose.evolution.yml up -d
```

**Step 2 — Open Manager UI**

Navigate to `http://localhost:8080/manager` in a browser.
Log in with the `AUTHENTICATION_API_KEY` you set in `.env.evolution`.

**Step 3 — Create an instance**

1. Click **"New Instance"**.
2. Enter a name (e.g. `turma-c`).
3. Leave defaults (Webhook can be configured after pairing).
4. Save — the instance now appears in the list.

**Step 4 — Read the QR code**

Option A — Manager UI: Click the instance → **Connect** → a QR code appears.

Option B — REST API:

```bash
curl -s http://localhost:8080/instance/connect/turma-c \
  -H "apikey: <your-evolution-api-key>" | jq .
```

Response includes a `base64` field with the QR image, or a `qrcode.url` string.

**Step 5 — Scan with WhatsApp**

On the phone:
1. Open WhatsApp → **Settings** → **Linked Devices**.
2. Tap **Link a Device**.
3. Scan the QR code displayed in the UI or render the `base64` in any QR viewer.

After successful scan, the instance status changes to `open` (connected).

**Step 6 — Validate the webhook**

Once paired, the instance can deliver messages to FastAPI. Send a test POST:

```bash
curl -s -X POST http://localhost:8000/api/v1/chatbot/webhook \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-webhook-token>" \
  -d '{"event":"messages.upsert","data":{"key":{"remoteJid":"5511999999999@s.whatsapp.net","fromMe":false},"message":{"conversation":"oi"}}}' | jq .
```

Expected: `{"status":"ok"}` (or a chatbot reply queued).

### 3.2 Instance Status Reference

| Status | Meaning | Action |
|---|---|---|
| `close` | Not connected, no QR yet | Click Connect to generate QR |
| `connecting` | QR generated, waiting for scan | Scan within 60 s |
| `open` | Connected | Normal operation |
| `disconnected` | Phone removed device / timeout | Re-scan QR (see Section 5, FM-5) |

---

## 4. Key Rotation

### 4.1 Rotating `EVOLUTION_API_KEY`

This is the master key for the Evolution Manager UI and REST API.

**Steps:**

1. Open `http://localhost:8080/manager` → **Settings** → **API Key**.
2. Click **Regenerate** (or **Reset Key**) — copy the new value immediately.
3. Update `.env.evolution`:
   ```dotenv
   AUTHENTICATION_API_KEY=<new-key>
   ```
4. Update root `.env`:
   ```dotenv
   EVOLUTION_API_KEY=<new-key>
   ```
5. Restart **only** the Evolution API container (Redis and Postgres can stay up):
   ```bash
   docker compose -f docker-compose.evolution.yml restart evolution_api
   ```
6. Confirm the Manager UI loads again with the new key.

### 4.2 Rotating `CHATBOT_WEBHOOK_TOKEN`

This token is the bearer secret Evolution uses to authenticate calls to FastAPI's webhook endpoint.

**Steps:**

1. Generate a new token (use a UUID or similar):
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Update root `.env`:
   ```dotenv
   CHATBOT_WEBHOOK_TOKEN=<new-token>
   ```
3. Restart FastAPI:
   ```bash
   # If running via docker compose (production-like)
   docker compose restart fastapi

   # If running via npm run dev (local)
   # Ctrl-C then npm run dev
   ```
4. Update the webhook URL configuration in the Evolution Manager UI (instance → Webhook → add `Authorization: Bearer <new-token>` header).
5. Validate:
   ```bash
   curl -s -X POST http://localhost:8000/api/v1/chatbot/webhook \
     -H "Authorization: Bearer <new-token>" \
     -H "Content-Type: application/json" \
     -d '{"event":"ping"}' | jq .
   ```
   Expected: `{"status":"ok"}` or `{"detail":"Unknown event"}` — either confirms the token was accepted (no 401).

---

## 5. Failure Modes

### FM-1: Evolution API returns 5xx

**Signals:**
- FastAPI broadcast endpoint returns `502` to the frontend.
- `docker compose -f docker-compose.evolution.yml ps` shows `evolution_api` as `unhealthy` or `restarting`.
- Log line: `connection refused: http://localhost:8080`

**Recovery:**

```bash
# Check container state
docker ps -a --filter name=evolution_api

# View recent logs
docker logs evolution_api --tail 50

# Restart the container
docker compose -f docker-compose.evolution.yml restart evolution_api

# If still failing, do a full down/up
docker compose -f docker-compose.evolution.yml down
docker compose -f docker-compose.evolution.yml up -d
```

---

### FM-2: DeepSeek 429 — Rate Limit

**Signals:**
- Chatbot returns: `"Serviço de IA temporariamente indisponível. Tente novamente mais tarde."`
- FastAPI log line: `evolution_api ERROR` or `429` in the AI provider call.
- `user_message` from `EvolutionApiError` will contain a sanitised rate-limit message (no internal paths).

**Recovery:**

1. Wait for the DeepSeek rate limit window to reset (typically 60 s or 1 min).
2. If persistent, check DeepSeek dashboard for quota exhaustion.
3. Consider increasing AI quota or switching `AI_MODEL` in `.env`.

---

### FM-3: Postgres Locked / Disk Full

**Signals:**
- Evolution API log: `FATAL: sorry, too many clients already` or `disk full`.
- `docker exec evolution_postgres pg_isready -U user` returns `no response`.
- Evolution Manager UI fails to load instances.

**Recovery:**

```bash
# Check disk space on the Docker volume host
df -h

# Connect to Postgres directly
docker exec -it evolution_postgres psql -U user -d evolution

# Check active connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

# Emergency: restart Postgres (brief downtime)
docker compose -f docker-compose.evolution.yml restart evolution_postgres

# If disk full, free space or expand volume before restarting
```

---

### FM-4: Docker Kill Mid-Broadcast (sanitised 502)

**Signals:**
- Broadcast POST returns `502` with a message like `"Erro ao enviar mensagem via WhatsApp."`.
- No internal paths, credentials, or stack traces in the response (Story 9.2 sanitisation is active).
- Partial broadcast: some students received the message, others did not.
- `docker ps` shows `evolution_api` stopped or restarting.

**Recovery:**

1. Restart the Evolution stack: `docker compose -f docker-compose.evolution.yml up -d`.
2. Check how many messages were sent (Evolution logs show per-JID delivery).
3. Re-send the broadcast — the professor interface shows the last status.

> **Note:** This is the documented behaviour from Story 9.2 chaos testing. The 502 is expected and intentional — it means the sanitisation contract is working correctly.

---

### FM-5: Evolution Instance Disconnected

**Signals:**
- Manager UI shows instance status as `disconnected` or `close`.
- WhatsApp was logged out on the phone, or the session expired.
- `GET /instance/connectionState/turma-c` returns `"state": "close"`.

**Recovery:**

```bash
# Check current state via API
curl -s http://localhost:8080/instance/connectionState/turma-c \
  -H "apikey: <your-evolution-api-key>" | jq .
```

Then re-pair following Section 3 (Pairing WhatsApp) from Step 4 onwards. The instance already exists — only re-scan is needed.

---

## 6. Log Locations & Grep Recipes

### 6.1 Log Locations

| Component | How to access |
|---|---|
| FastAPI | `docker compose logs fastapi -f` (or `journalctl -u fastapi` in production systemd) |
| Evolution API | `docker logs evolution_api -f` |
| Postgres | `docker logs evolution_postgres -f` |
| Redis | `docker logs evolution_redis -f` |
| Local dev | Terminal running `npm run dev` — `[backend]` prefix lines |

### 6.2 Grep Recipes

**Webhook hits (incoming messages from Evolution):**

```bash
docker compose logs fastapi 2>&1 | grep "POST /api/v1/chatbot/webhook"
```

Expected line:

```
INFO:     172.18.0.1:55432 - "POST /api/v1/chatbot/webhook HTTP/1.1" 200 OK
```

---

**Evolution API errors (5xx, connection issues):**

```bash
docker logs evolution_api 2>&1 | grep -iE "error|exception|fatal"
```

---

**Rate-limit hits (per-phone daily limit reached):**

```bash
docker compose logs fastapi 2>&1 | grep "rate.limit\|RATE_LIMIT\|blocked"
```

Or search for the HTTP 429 response in the chatbot router:

```bash
docker compose logs fastapi 2>&1 | grep "429"
```

---

**Sanitisation leak check (CRITICAL — should return nothing):**

```bash
docker compose logs fastapi 2>&1 | grep -iE "traceback|/etc/|/var/log|docker |kubectl|ssh "
```

If this grep returns ANY output, a sanitisation regression has occurred. File a bug immediately and check `EvolutionApiError._INTERNAL_LEAK_PATTERNS` (Section 8).

---

**Postgres FATAL errors:**

```bash
docker logs evolution_postgres 2>&1 | grep -E "FATAL|ERROR|panic"
```

---

**Broadcast sends (professor sends message to class):**

```bash
docker compose logs fastapi 2>&1 | grep "broadcast\|POST /api/v1/broadcast"
```

---

## 7. Backup / Restore Postgres

### 7.1 Manual Backup

```bash
# Creates backup-YYYY-MM-DD.sql in the current directory
docker exec evolution_postgres pg_dump -U user evolution > backup-$(date +%F).sql
```

Verify the file was created and is non-empty:

```bash
ls -lh backup-$(date +%F).sql
# Expected: file size > 10 KB (depends on data volume)
```

### 7.2 Restore

```bash
# Restore from a backup file
cat backup-2026-06-10.sql | docker exec -i evolution_postgres psql -U user evolution
```

> **Note:** This is additive by default. For a clean restore, drop and recreate the DB first:
> ```bash
> docker exec evolution_postgres psql -U user -c "DROP DATABASE evolution; CREATE DATABASE evolution;"
> cat backup-2026-06-10.sql | docker exec -i evolution_postgres psql -U user evolution
> ```

### 7.3 Integrity Check

After restore, verify key tables are populated:

```bash
docker exec evolution_postgres psql -U user -d evolution -c "SELECT count(*) FROM instances;"
docker exec evolution_postgres psql -U user -d evolution -c "SELECT count(*) FROM messages;"
```

### 7.4 Runnable Backup Script

Save as `scripts/backup-evolution-db.sh`:

```bash
#!/usr/bin/env bash
# Evolution Postgres backup script — Story 9.3
# Usage: ./scripts/backup-evolution-db.sh [BACKUP_DIR]
# Keeps 7 daily and 4 weekly backups.

set -euo pipefail

BACKUP_DIR="${1:-./backups/evolution}"
mkdir -p "$BACKUP_DIR"

DATE=$(date +%F)
DAY_OF_WEEK=$(date +%u)  # 1=Mon … 7=Sun
DAILY_FILE="$BACKUP_DIR/daily-$DATE.sql"
WEEKLY_FILE="$BACKUP_DIR/weekly-$(date +%Y-W%V).sql"

echo "[backup] Dumping evolution DB → $DAILY_FILE"
docker exec evolution_postgres pg_dump -U user evolution > "$DAILY_FILE"
echo "[backup] Done. Size: $(du -sh "$DAILY_FILE" | cut -f1)"

# Copy to weekly on Sundays
if [ "$DAY_OF_WEEK" -eq 7 ]; then
  cp "$DAILY_FILE" "$WEEKLY_FILE"
  echo "[backup] Weekly copy → $WEEKLY_FILE"
fi

# Prune: keep 7 daily
ls -t "$BACKUP_DIR"/daily-*.sql 2>/dev/null | tail -n +8 | xargs -r rm --
echo "[backup] Kept last 7 daily backups."

# Prune: keep 4 weekly
ls -t "$BACKUP_DIR"/weekly-*.sql 2>/dev/null | tail -n +5 | xargs -r rm --
echo "[backup] Kept last 4 weekly backups."
```

Make executable:

```bash
chmod +x scripts/backup-evolution-db.sh
```

### 7.5 Cron Schedule (server/Linux)

```cron
# Run daily at 02:00 — adjust path to project root
0 2 * * * /path/to/project/scripts/backup-evolution-db.sh /path/to/backups >> /var/log/evolution-backup.log 2>&1
```

---

## 8. Sanitisation Contract

> Implemented in Story 9.2. Source: `backend/app/services/evolution_api_client.py`

### 8.1 What It Does

`EvolutionApiError.user_message` is the **only** error message string that may be sent to end users (students, professor UI, or API callers). It is:

1. Truncated to **120 characters**.
2. Stripped of any text that contains the 10 internal leak patterns listed below.
3. Replaced with a generic fallback if the original message is too dangerous to expose.

### 8.2 The 10 Patterns (verbatim)

| # | Pattern | What it prevents leaking |
|---|---|---|
| 1 | `"docker "` | Docker daemon errors, container names |
| 2 | `"dockerfile"` | Build configuration details |
| 3 | `"/var/log"` | Server filesystem paths |
| 4 | `"/etc/"` | Config file paths (credentials, hosts) |
| 5 | `"traceback"` | Python stack traces |
| 6 | `"stack trace"` | Generic stack trace references |
| 7 | `"exception:"` | Raw exception messages |
| 8 | `"connection refused:"` | Internal service topology |
| 9 | `"kubectl"` | Kubernetes cluster information |
| 10 | `"ssh "` | SSH command details |

### 8.3 Verification

To confirm sanitisation is active, send a request that triggers an Evolution API error and inspect the response body:

```bash
# Simulate a bad instance call (wrong instance name)
curl -s -X POST http://localhost:8000/api/v1/broadcast/ \
  -H "Authorization: Bearer <professor-token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "instance": "nonexistent"}' | jq .detail
```

The response `detail` should be a short user-friendly message, NOT contain any of the 10 patterns above.

**Leak check (should return nothing):**

```bash
curl -s -X POST http://localhost:8000/api/v1/broadcast/ \
  -H "Authorization: Bearer <professor-token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "instance": "nonexistent"}' \
  | grep -iE "traceback|docker |/etc/|/var/log|kubectl|ssh "
```

If this grep returns output: **sanitisation regression** — open a P0 bug.

### 8.4 What Operators See on a Sanitised 502

A broadcast 502 response looks like:

```json
{
  "detail": "Erro ao enviar mensagem via WhatsApp."
}
```

This is the generic fallback. The full error is available in FastAPI logs (never in the HTTP response).

---

## 9. Rate Limiting

> Implemented in Story 3.4. Source: `backend/app/services/chatbot_rate_limiter.py`

### 9.1 Default Configuration

| Setting | Value | Where defined |
|---|---|---|
| Daily limit per phone | **10 messages** | `ChatbotRateLimiter(daily_limit=10)` |
| Window | Calendar day (UTC date string) | `_counters` key = `{phone}:{YYYY-MM-DD}` |
| Storage | In-memory Python dict | `ChatbotRateLimiter._counters` |
| Scope | Per normalised phone number | `normalized_phone` parameter |

### 9.2 How It Works

```python
class ChatbotRateLimiter:
    def __init__(self, daily_limit: int = 10) -> None:
        self.daily_limit = daily_limit
        self._counters = {}  # {phone: {date: count}}

    def is_blocked(self, normalized_phone: str) -> bool:
        """Returns True if phone >= daily_limit messages today."""

    def record(self, normalized_phone: str) -> None:
        """Increment counter for phone."""
```

When `is_blocked()` returns `True`, the webhook handler rejects the message with a 429-equivalent response and the student receives the configured rate-limit message.

### 9.3 Adjusting the Limit

The limit is set at instantiation time. To change it:

1. Find the `ChatbotRateLimiter` instantiation in `backend/app/routers/chatbot.py` (or wherever the dependency is injected).
2. Change the `daily_limit` argument:
   ```python
   rate_limiter = ChatbotRateLimiter(daily_limit=20)  # Allow 20/day
   ```
3. Restart FastAPI.

> **Note:** The counter is in-memory — it resets on every FastAPI restart. For persistent rate limiting across restarts, a Redis-backed implementation would be needed (out of scope).

### 9.4 Inspecting Counters at Runtime

In a development/debugging session, you can attach to the running FastAPI process and inspect `_counters`. More practically, grep the logs:

```bash
docker compose logs fastapi 2>&1 | grep "rate"
```

Or add a temporary debug log line in `chatbot_rate_limiter.py`:

```python
logger.debug("Rate counters: %s", self._counters)
```

---

## 10. Architecture Reference

### 10.1 Epic Docs

| Document | Path | Contents |
|---|---|---|
| Epic 6 PRD | `docs/prd/` | AI WhatsApp Chatbot requirements (FR17-FR20) |
| Epic 8 architecture | `docs/architecture/` | Full stack design — Evolution integration |
| Epic 9 acceptance | `docs/qa/evolution-acceptance-9.1.md` | E2E operator transcript (~620 lines, signed attestation) |
| Epic 9 chaos | `docs/qa/chaos-test-9.2.md` | 5-scenario chaos test transcript |

### 10.2 Key Source Files

| File | Role |
|---|---|
| `backend/app/services/evolution_api_client.py` | Evolution REST client, `EvolutionApiError`, sanitisation (line ~37+) |
| `backend/app/services/chatbot_rate_limiter.py` | Per-phone daily rate limiter |
| `backend/app/routers/professor.py:225` | `POST /api/v1/broadcast/` — broadcast endpoint |
| `backend/app/routers/chatbot.py` | `POST /api/v1/chatbot/webhook` — incoming message handler |
| `docker-compose.evolution.yml` | Three-service Evolution stack definition |
| `.env.evolution` | Evolution API container env (not committed) |

### 10.3 API Endpoints Summary

| Method + Path | Auth | Purpose |
|---|---|---|
| `POST /api/v1/broadcast/` | Professor JWT | Send message to all students |
| `POST /api/v1/chatbot/webhook` | Bearer token | Receive messages from Evolution |
| `GET /instance/connect/{instance}` | Evolution API key | Get QR code for pairing |
| `GET /instance/connectionState/{instance}` | Evolution API key | Check instance connection status |

### 10.4 Story Trail

- **Story 9.0:** Epic setup, `.env.evolution` template, docker compose skeleton
- **Story 9.1:** Real Evolution `send_whatsapp_text` integration — E2E confirmed (see `docs/qa/evolution-acceptance-9.1.md`)
- **Story 9.2:** Broadcast chaos + `EvolutionApiError` sanitisation hardening (see `docs/qa/chaos-test-9.2.md`)
- **Story 9.3:** This runbook

---

## 11. Change Log

| Date | Author | Change |
|---|---|---|
| 2026-06-10 | @dev (Dex) | Initial runbook created — Story 9.3. Covers all 10 ACs: bring-up, pairing, key rotation, 5 failure modes, log locations, backup/restore, sanitisation contract, rate limiting, architecture reference. |
