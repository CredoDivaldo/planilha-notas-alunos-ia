# System Architecture

> Nota de alinhamento: `docs/architecture.md` é o artefacto formal brownfield e fonte decisória para o Epic 5. Esta página permanece como contexto técnico, visão alvo resumida e avaliação histórica.

## Architecture Target State

### Summary
O produto deixa de ser um MVP de upload e disparo por WhatsApp e passa a ser uma plataforma académica com persistência real, publicação controlada e múltiplos papéis operacionais. Esta secção define a arquitectura alvo; o assessment histórico abaixo continua útil como fotografia do estado anterior.

### Target Architecture Drivers
- Base de dados real como fonte de verdade.
- Python obrigatório como linguagem relevante da solução.
- Modelo académico explícito: semestre, turno, turma, disciplina, professor e estudante.
- Publicação controlada por broadcast.
- Portal do estudante com autenticação.
- Permissões distintas para professor, delegado e estudante.

### Proposed Technical Direction

#### Option A — Preferred
- Backend principal em Python.
- API web em Python.
- Motor académico, importação estruturada, cálculo e publicação no mesmo stack.
- Formalizada em `docs/architecture.md` como FastAPI + SQLite.

#### Option B — Transitional
- Manter parte do backend actual temporariamente.
- Introduzir Python para motor académico, importação, validação e cálculo.
- Migrar progressivamente o restante backend para arquitectura coerente.
- Mantida apenas como estratégia de coexistência brownfield, não como alvo final.

### Proposed Logical Modules
- `identity` — autenticação, sessão e mudança obrigatória de palavra-passe no primeiro acesso.
- `academic-registry` — semestres, turnos, turmas, disciplinas, cursos e alocações docentes.
- `student-registry` — estudantes, contactos, password inicial e papel de delegado.
- `grade-ingestion` — importação CSV/XLSX e validação de ficheiros.
- `grade-management` — edição manual, correcções e regras de acesso.
- `academic-engine` — cálculo de estado académico com fórmula configurável.
- `publication-service` — transição de dados internos para estado publicado.
- `calendar-service` — gestão de provas, exames e recursos.
- `notification-service` — WhatsApp e e-mail.
- `audit-log` — rastreio de uploads, edições, broadcasts e aprovações.

### Domain Model
- `Student`: número de estudante, identidade, contactos, password, curso/turma actual.
- `Professor`: identidade do docente e contexto(s) configurado(s).
- `DelegateAssignment`: marca um estudante como delegado de uma turma específica.
- `Semester`: período lectivo explícito.
- `Shift`: manhã, tarde ou noite.
- `ClassGroup`: turma.
- `Subject`: disciplina.
- `TeachingAssignment`: relação professor + turma + disciplina + semestre + turno.
- `Enrollment`: vínculo estudante + contexto académico.
- `AssessmentDefinition`: prova, exame, recurso e componentes contínuos.
- `GradeEntry`: valores lançados por estudante.
- `PublishedGradeSnapshot`: versão publicada ao estudante após broadcast.
- `CalendarEvent`: prova, exame ou recurso com data e contexto.
- `BroadcastJob`: operação manual de publicação.
- `NotificationDelivery`: rastreio de envio por canal.

### Publication Flow
1. Professor ou delegado autorizado prepara dados.
2. Professor importa ou corrige notas.
3. Sistema calcula estado interno, sem expor ao estudante.
4. Professor executa broadcast manual.
5. Sistema cria snapshot publicada.
6. Portal do estudante passa a exibir apenas a versão publicada mais recente.
7. Alterações posteriores exigem novo broadcast.

### Delegate Safety Model
- Delegado pode operar apenas dentro da turma onde foi autorizado.
- Delegado pode adicionar/actualizar dados básicos de estudantes.
- Delegado pode ajudar em uploads e preparação de broadcasts.
- Alterações sensíveis devem exigir confirmação explícita do professor.
- Todas as acções do delegado devem ficar auditadas.

### Authentication and Access
- Estudante: número de estudante + palavra-passe.
- Primeiro acesso: troca obrigatória de palavra-passe.
- Professor: conta individual própria.
- Delegado: autentica-se como estudante, mas recebe permissões técnicas adicionais quando existir atribuição activa.

### Data and Persistence
- Migrar persistência operacional de JSON para base de dados relacional.
- Manter JSON apenas como artefacto transitório ou cache, não como fonte de verdade.
- Preparar esquema para múltiplas disciplinas por estudante no mesmo semestre.
- Suportar consultas por estudante, por turma, por disciplina e por semestre.

### Integration Architecture
- WhatsApp: canal primário de publicação e notificação.
- E-mail: canal secundário opcional.
- Portal web: canal de consulta pós-publicação.
- Importação estruturada: CSV no mínimo; XLS/XLSX como extensão provável.

### AI Provider Architecture

**Overview:**
Respostas de IA do chatbot são geradas via API externa, configurável sem alterações de código.

**Provider Padrão: Baidu QianFan** (DEPRECATED 2026-06-08 — switched to DeepSeek in Story 9.0)
- Free tier: 100K tokens/mês (suficiente para MVP)
- Linguagens: Suporte excelente para Português + Chinês
- Latência: 150-300ms (aceitável para fluxo assíncrono WhatsApp)
- Confiabilidade: 99.5% SLA (free tier)

**Configuration (Variáveis de Ambiente) — Baidu (DEPRECATED):**

| Variável | Exemplo | Notas |
|----------|---------|-------|
| `BAIDU_API_KEY` | `ERNIE-Bot-xxx` | Obrigatório (free tier account) |
| `BAIDU_MODEL` | `ERNIE-3.5` | Free tier (ERNIE-4.0 = pago, fora de escopo) |

**Vantagens da Baidu QianFan:**
- ✅ Zero custo (free tier com quota generosa)
- ✅ Qualidade nativa em Português
- ✅ Sem dependências complexas de SDK externas
- ✅ Setup rápido para contas internacionais

---

**Provider Padrão: DeepSeek Chat** (Story 9.0 — current, 2026-06-08)
- API: OpenAI-compatible, base URL `https://api.deepseek.com`
- Custo: ~$0.14/M tokens (chat), ~$0.28/M tokens (output) — acessível para MVP
- Linguagens: Suporte robusto para Português (modelo deepseek-chat treinado em PT)
- Latência: 200-500ms (aceitável para fluxo assíncrono WhatsApp)
- SDK: reutiliza `openai` Python client (já em `pyproject.toml`); zero deps novas

**Configuration (Variáveis de Ambiente) — DeepSeek (current):**

| Variável | Exemplo | Notas |
|----------|---------|-------|
| `DEEPSEEK_API_KEY` | `sk-xxx` | Obrigatório (https://platform.deepseek.com/api_keys) |
| `AI_MODEL` | `deepseek-chat` | Default; OpenAI-compatible model ID |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | Opcional, default OK |

**Vantagens da DeepSeek:**
- ✅ Custo muito baixo (~$0.14/M tokens)
- ✅ Suporte multilingual forte, incluindo Português
- ✅ Compatibilidade OpenAI (reutiliza SDK já no projecto)
- ✅ Sem mudanças estruturais — drop-in via `AIProvider` ABC
- ✅ Tráfego de produção real (não free-tier instável)

**Características de Segurança:**
- System prompt restringe respostas a contexto de notas publicadas apenas
- Rate limiting (10 msgs/dia por estudante) mantém uso dentro free tier
- Fallback message em caso de falha de API
- Logs estruturados de todas as interações

### Architecture Risks
- Fórmula oficial de cálculo ainda indefinida.
- Transição de permissões do delegado pode gerar complexidade operacional.
- Migração parcial entre runtime actual e Python pode criar duplicação temporária.
- Publicação dependente de broadcast exige modelo claro de estados para evitar inconsistência.

### Decisões Formalizadas e Pendências
1. Ponto de entrada Python formalizado em `docs/architecture.md`: FastAPI em `backend/app/main.py`.
2. Base de dados formalizada em `docs/architecture.md`: SQLite local com Alembic.
3. Estratégia de migração formalizada em `docs/architecture.md`: JSON legado/coexistente, importação sem remoção automática.
4. Esquema inicial de publicação formalizado em `docs/architecture.md`: snapshots ligados a broadcast.
5. Pendência de produto: fluxo exacto de aprovação do delegado.

---

# Historical Assessment

**Project:** Planilha Notas Alunos IA
**Date:** 2026-05-02
**Assessment Type:** Complete Technical Audit (Due Diligence)
**Assessor:** @architect (Aria)

---

## Executive Summary

MVP local para importação de notas de alunos via CSV e disparo de mensagens WhatsApp através da Evolution API. Sistema simples, bem estruturado, com **débitos técnicos moderados** — foco principal em segurança, testes e documentação.

| Métrica | Valor |
|---------|-------|
| Total de Débitos | 12 |
| Críticos | 2 |
| Altos | 4 |
| Médios | 6 |
| Baixos | 0 |
| Esforço Total Estimado | ~24 horas |

---

## 1) Visão Geral

O projecto é um MVP monolítico Node.js/Express com frontend estático (HTML/CSS/JS) servido pelo próprio backend. O fluxo principal é: upload de CSV de estudantes e notas, geração de match entre dados, e envio em massa de mensagens via Evolution API (WhatsApp).

## 2) Stack Tecnológico Real
- Runtime/Backend: Node.js + Express (`package.json`)
- Middleware/API: `cors`, `multer`, `express.json` (`src/server.js`)
- Parsing CSV: `csv-parse/sync` (`src/services/csv-parser.js`)
- Configuração: `dotenv` (`src/server.js`, `src/services/evolution-client.js`)
- Frontend: estático em `public/` (`index.html`, `app.js`, `styles.css`)
- Persistência local: ficheiros JSON em `data/` via `fs/promises` (`src/services/storage.js`)
- Integração externa: Evolution API via HTTP (`src/services/evolution-client.js`)
- Tooling: scripts npm simples, sem lint/test/typecheck configurados (`package.json`)

## 3) Estrutura Actual e Responsabilidades
- `src/server.js`: bootstrap HTTP, middlewares globais, rotas `/api/*`, healthcheck e error handler.
- `src/routes/`
  - `students.js`: upload/listagem de estudantes.
  - `grades.js`: upload/listagem de notas.
  - `match.js`: geração e leitura de match.
  - `send.js`: disparo em massa (real/simulado).
  - `evolution.js`: operações de instância Evolution (create/connect/state).
- `src/services/`
  - `csv-parser.js`: parsing e normalização de payloads CSV.
  - `matcher.js`: algoritmo de matching e validação de telefone.
  - `storage.js`: leitura/escrita JSON local.
  - `evolution-client.js`: cliente HTTP da Evolution API e template de mensagem.
- `public/`: UI única com 5 passos operacionais (upload → match → conexão → disparo).

## 4) Fluxos Funcionais Existentes
1. Upload estudantes: `POST /api/v1/students/upload` (FastAPI) → parse/normaliza → grava em `legacy_students` (SQLite via SQLAlchemy).
2. Upload notas: `POST /api/v1/grades/upload` (FastAPI) → parse/normaliza → grava em `legacy_grades` (SQLite via SQLAlchemy).
3. Match: `POST /api/v1/match/generate` (FastAPI) → `buildMatch` → devolve match em memória (sem persistência intermédia em JSON desde o cutover da Story 8.4).
4. Evolution: create/connect/state via `/api/evolution/instance/*`.
5. Envio em massa: `POST /api/send/bulk` com `template` e `dryRun`.

## 5) Configuração e Integrações
Variáveis de ambiente detectadas no cliente Evolution:
- `APP_PORT`
- `EVOLUTION_BASE_URL`
- `EVOLUTION_API_KEY`
- `EVOLUTION_INSTANCE`
- `EVOLUTION_INTEGRATION` (default `WHATSAPP-BAILEYS`)

Integração de infraestrutura por Docker Compose:
- `docker-compose.evolution.yml`
- `docker-compose.evolution-lite.yml`

## 6) Inventário de Débitos Técnicos

### CRITICAL (Priority 1)

#### TD-001: Config Evolution API sem validação startup
**Location:** `src/services/evolution-client.js:3-14`
**Issue:** API credentials loaded from `.env` without validation at startup
**Impact:** Runtime failures if config incomplete; no early warning
**Effort:** 2h
**Recommendation:** Add startup validation + config health endpoint

#### TD-002: No Input Validation on CSV Upload
**Location:** `src/routes/students.js:22-29`, `src/routes/grades.js`
**Issue:** No validation of CSV structure, field types, or size limits
**Impact:** Malformed CSV causes runtime errors; potential injection
**Effort:** 3h
**Recommendation:** Add schema validation (e.g., Joi, Zod) for CSV fields

---

### HIGH (Priority 2)

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

#### TD-005: Missing Authentication/Authorization
**Location:** All routes
**Issue:** No auth mechanism; anyone can access API
**Impact:** Unauthorized access to student data; message spoofing
**Effort:** 4h
**Recommendation:** Add basic auth or JWT; at minimum API key

#### TD-006: Error Messages Leak Internal Info
**Location:** `src/app.js:27-32`
**Issue:** Error handler exposes internal errors on 5xx
**Impact:** Information disclosure to attackers
**Effort:** 0.5h
**Recommendation:** Sanitize error messages; log internally only

---

### MEDIUM (Priority 3)

#### TD-007: Missing Request Logging
**Location:** `src/app.js`
**Issue:** No request logging middleware
**Impact:** Difficult debugging; no audit trail
**Effort:** 1h
**Recommendation:** Add `morgan` or custom logger

#### TD-008: Frontend Has No Error Handling UI
**Location:** `public/app.js`
**Issue:** Frontend likely lacks proper error states
**Impact:** Poor UX on failures; no feedback to user
**Effort:** 2h
**Recommendation:** Add error states, loading indicators

#### TD-009: No Database (JSON Files) — RESOLVED in Story 8.4
**Location (resolvido):** `data/*.json` → `legacy/data/*.json` (movido em Story 8.4)
**Issue (resolvido):** JSON files not suitable for concurrent access, querying
**Resolution:** cutover para SQLite via SQLAlchemy em `backend/app/app.sqlite3` — produção lê exclusivamente do DB. O subcommand `python -m backend.app.cli migrate-legacy-csv <dir>` re-importa CSVs de demo a partir de `legacy/fixtures/` para o DB.

#### TD-010: Test Coverage Limited
**Location:** `tests/critical-flow.test.js`
**Issue:** Only one test file; no edge case coverage
**Impact:** Hidden bugs; regression risk
**Effort:** 3h
**Recommendation:** Add tests for: validation, errors, phone normalization

#### TD-011: Missing API Documentation
**Location:** Project root
**Issue:** No OpenAPI/Swagger spec
**Impact:** Integration difficulty; maintenance burden
**Effort:** 2h
**Recommendation:** Add OpenAPI spec + Swagger UI

#### TD-012: No Environment Configuration Docs
**Location:** Project
**Issue:** `.env` structure not documented
**Impact:** Setup difficulty; wrong configurations
**Effort:** 0.5h
**Recommendation:** Add `.env.example` + README section

## 7) Banco de Dados — Situação Actual
Não há evidência de base de dados local (SQL/ORM/migrations/schema) no projecto actual.

Evidências:
- Não foram encontrados ficheiros `.sql`, `prisma`, `supabase/`, nem ficheiros de base local.
- Persistência operacional implementada em ficheiros JSON na pasta `data/` (`src/services/storage.js`).
- Há integração Docker para Evolution API, mas isso não representa DB de aplicação.

---

## 7) Security Assessment

| Check | Status | Notes |
|-------|--------|-------|
| Input validation | ❌ FAIL | No CSV schema validation |
| Authentication | ❌ FAIL | No auth mechanism |
| Rate limiting | ❌ FAIL | No limits |
| Error sanitization | ❌ FAIL | Internal errors exposed |
| Secrets management | ✅ PASS | Uses `.env` (not committed) |
| CORS | ✅ PASS | Enabled (may need restriction) |
| File upload limits | ⚠️ PARTIAL | Multer default limits; no explicit config |

**Overall Security Score: 3/10 — CRITICAL improvements needed**

---

## 8) Strengths

- **Clean code structure:** Routes/services separation is solid
- **Async error handling:** `asyncHandler` wrapper is good pattern
- **Test exists:** At least one integration test covering main flow
- **Dry run mode:** `send/bulk` has `dryRun` option — safe testing
- **Phone normalization:** Good validation for WhatsApp numbers
- **Docker setup:** Evolution API properly containerized
- **Husky hooks:** Pre-commit quality gates present

---

## 9) Recomendações Prioritárias

| Priority | Debt ID | Effort | ROI |
|----------|---------|--------|-----|
| 1 | TD-002 | 3h | HIGH — Prevents injection, crashes |
| 1 | TD-001 | 2h | HIGH — Prevents runtime failures |
| 2 | TD-005 | 4h | HIGH — Prevents unauthorized access |
| 2 | TD-006 | 0.5h | HIGH — Security fix, quick |
| 2 | TD-003 | 2h | MEDIUM — Data integrity |
| 2 | TD-004 | 1h | MEDIUM — Prevents abuse |
| 3 | TD-010 | 3h | MEDIUM — Reduces bugs |
| 3 | TD-007 | 1h | LOW — Improves debugging |

---

## 10) Banco de Dados — Situação Actual
Não há evidência de base de dados local (SQL/ORM/migrations/schema) no projecto actual.

Evidências:
- Não foram encontrados ficheiros `.sql`, `prisma`, `supabase/`, nem ficheiros de base local.
- Persistência operacional implementada em ficheiros JSON na pasta `data/` (`src/services/storage.js`).
- Há integração Docker para Evolution API, mas isso não representa DB de aplicação.

---

## 11) Próximos Passos (Workflow)

- **FASE 2 (Database):** SKIPPED (condition: `project_has_database = false`)
- **FASE 3 (Frontend/UX):** Seguir com @ux-design-expert → `*create-front-end-spec`
- **FASE 4:** Consolidar DRAFT com Database marcado como “não aplicável”

---

*Assessment completed by Aria (@architect) — 2026-05-02*
