# System Architecture — Brownfield Discovery (Fase 1)

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
1. Upload estudantes: `POST /api/students/upload` → parse/normaliza → grava `data/students.json`.
2. Upload notas: `POST /api/grades/upload` → parse/normaliza → grava `data/grades-last-upload.json`.
3. Match: `POST /api/match/generate` → `buildMatch` → grava `data/match-last.json`.
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

## 6) Evidências de Débito Técnico (nível sistema)
1. Ausência de suíte de qualidade automatizada (lint/test/typecheck) no npm scripts.
   - Evidência: `package.json` (scripts apenas `dev`, `start`, `prepare`, `evolution:*`).
2. Persistência baseada em ficheiro JSON sem controlo de concorrência/versionamento.
   - Evidência: `src/services/storage.js` usa `fs.writeFile` directo para artefactos críticos.
3. Backend sem validação estrutural de entrada (schema validation).
   - Evidência: rotas aceitam payloads com validação mínima (`src/routes/send.js`, `src/routes/students.js`, `src/routes/grades.js`).
4. UI sem camada modular/componentização e sem gestão explícita de estados complexos.
   - Evidência: lógica concentrada em `public/app.js` com fluxo completo num único ficheiro.
5. Acoplamento directo entre rota e integração externa (Evolution) sem abstrações de domínio.
   - Evidência: `src/routes/send.js` chama cliente externo directamente para cada item.
6. Tratamento de erro genérico no servidor, sem classificação/log estruturado.
   - Evidência: `src/server.js` retorna `500` genérico no middleware global.

## 7) Banco de Dados — Situação Actual
Não há evidência de base de dados local (SQL/ORM/migrations/schema) no projecto actual.

Evidências:
- Não foram encontrados ficheiros `.sql`, `prisma`, `supabase/`, nem ficheiros de base local.
- Persistência operacional implementada em ficheiros JSON na pasta `data/` (`src/services/storage.js`).
- Há integração Docker para Evolution API, mas isso não representa DB de aplicação.

## 8) Recomendações Imediatas (para continuidade do workflow)
- Seguir para Fase 3 (Frontend/UX) e pular Fase 2 (Database) por condição `project_has_database = false`.
- Na Fase 4, consolidar DRAFT já com secção de Database marcada como “não aplicável neste momento”.
- Priorizar stories iniciais para: validação de inputs, observabilidade mínima, e baseline de testes.
