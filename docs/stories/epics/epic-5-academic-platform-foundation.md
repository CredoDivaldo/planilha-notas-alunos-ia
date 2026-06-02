# Epic 5: Academic Platform Foundation

**Epic ID:** EPIC-5  
**Status:** Draft  
**Created:** 2026-05-26  
**Updated:** 2026-05-28  
**Owner:** @pm (Morgan)  

---

## Overview

Transformar o MVP actual numa plataforma académica com backend principal em Python/FastAPI, base de dados local SQLite, migrações Alembic e modelo de domínio capaz de suportar turmas, disciplinas, semestres, turnos, cálculo académico configurável, publicação controlada e portal do estudante.

## Business Context

O backlog anterior deixou de representar o produto real. O sistema agora precisa de:
- usar Python/FastAPI como backend principal;
- abandonar ficheiros JSON como persistência académica principal, mantendo-os como legado/coexistência durante a transição;
- suportar múltiplos papéis: professor, delegado e estudante;
- consolidar notas por número de estudante;
- publicar notas apenas após broadcast explícito;
- preparar portal do estudante e calendário académico com leitura exclusiva de snapshots publicados.

Sem esta fundação, qualquer evolução de frontend, testes ou integrações continuará assente num modelo de dados insuficiente para o produto académico pretendido.

## Scope

### IN
- Backend principal em Python/FastAPI em `backend/app/main.py`.
- API nova versionada sob `/api/v1`.
- Base de dados local SQLite em `data/app.sqlite3`.
- Migrações Alembic em `backend/migrations/`.
- Modelo académico base.
- Autenticação, sessões server-side, papéis iniciais e Argon2id.
- Motor inicial configurável de lançamento/publicação de notas.
- Snapshots imutáveis ligados a `broadcast_jobs`.
- Configuração de contextos académicos pelo professor.
- Modelo de leitura do portal do estudante.
- Regressão obrigatória do fluxo Node legado.

### OUT
- Fórmula académica final institucional fechada.
- Fluxo operacional final de aprovação de acções assistidas pelo delegado.
- Canal/cerimónia final de entrega da palavra-passe inicial do estudante.
- UX refinada do portal.
- Analytics e relatórios avançados.
- Infraestrutura cloud, CI/CD remoto, canary, blue/green e produção multiambiente.

## Success Criteria

| Criteria | Metric |
|----------|--------|
| Python adopted | Backend principal e serviços centrais em FastAPI |
| Local database | Persistência académica principal em SQLite, fora de JSON |
| Academic model | Suporte a semestre, turno, turma, disciplina, estudante e professor |
| Roles | Professor, delegado e estudante modelados com limites explícitos |
| Publication control | Notas visíveis apenas após broadcast e snapshot publicado |
| Portal read model | Estudante consulta apenas snapshots actuais publicados |
| Regression safety | `npm run lint`, `npm run typecheck` e `npm test` continuam a passar |
| Story readiness | Backlog fundacional pronto para implementação incremental |

## Dependencies

- `docs/prd.md` actualizado.
- `docs/architecture.md` como fonte arquitectural principal.
- `docs/api/README.md` regista política OpenAPI enquanto o backend Python ainda não existe.
- Documentos leves em `docs/framework/` apontam para arquitectura como fonte temporária de standards.

## Open Product Decisions

Estas decisões não ficam fechadas por este epic e não devem ser inventadas durante implementação:

1. Fórmula oficial de cálculo académico e estados derivados.
2. Fluxo exacto de aprovação/validação de acções assistidas pelo delegado.
3. Canal e cerimónia exactos para entrega da palavra-passe inicial do estudante.

As stories devem permanecer testáveis usando fórmula configurável, estados de validação pendentes/aprovados/rejeitados, hash de palavra-passe temporária e registo de entrega sem segredo em claro.

## Story Sequencing

### Sequência recomendada

1. **Story 5.1** estabelece FastAPI, SQLite, Alembic, `/api/v1`, qualidade Python e compatibilidade Node.
2. **Story 5.2** usa a fundação da 5.1 para autenticação, sessões, papéis e limites de delegado.
3. **Story 5.4** usa 5.1/5.2 para contextos académicos e escopo de upload.
4. **Story 5.3** usa 5.1/5.2/5.4 para notas internas, cálculo configurável, broadcast e snapshots.
5. **Story 5.5** usa 5.1-5.4 para portal read-only baseado em snapshots publicados.

Stories 5.2-5.4 podem ser preparadas em paralelo como desenho/tarefas, mas implementação executável deve respeitar dependências de DB/API da 5.1.

## Stories

### Story 5.1: Python Backend and Local Database Foundation
- **Points:** 5
- **Owner:** @dev
- **Priority:** P0
- **Description:** Criar backend FastAPI, SQLite local, Alembic, `/api/v1`, OpenAPI runtime e compatibilidade com Node legado
- **File:** `docs/stories/5.1.python-backend-local-database-foundation.md`

### Story 5.2: Authentication and Role Foundation
- **Points:** 5
- **Owner:** @dev
- **Priority:** P0
- **Description:** Introduzir autenticação, sessões server-side, Argon2id, primeiro acesso obrigatório e papéis professor/delegado/estudante
- **File:** `docs/stories/5.2.authentication-and-role-foundation.md`

### Story 5.3: Grade Publication Workflow Foundation
- **Points:** 5
- **Owner:** @dev
- **Priority:** P0
- **Description:** Modelar notas internas, cálculo configurável, snapshots publicados, broadcast jobs e entregas
- **File:** `docs/stories/5.3.grade-publication-workflow-foundation.md`

### Story 5.4: Professor Academic Context Setup
- **Points:** 4
- **Owner:** @dev
- **Priority:** P0
- **Description:** Permitir que o professor configure contextos `turma + disciplina + semestre + turno` com escopo de upload
- **File:** `docs/stories/5.4.professor-academic-context-setup.md`

### Story 5.5: Student Portal Read Model Foundation
- **Points:** 4
- **Owner:** @dev
- **Priority:** P1
- **Description:** Preparar modelo de leitura do portal do estudante para notas publicadas e calendário
- **File:** `docs/stories/5.5.student-portal-read-model-foundation.md`

## Timeline

- **Sprint 1:** Story 5.1.
- **Sprint 2:** Stories 5.2 e 5.4, respeitando fundação de DB/API.
- **Sprint 3:** Story 5.3.
- **Sprint 4:** Story 5.5.
- **Effort Total:** 23 points.

## Rollback, Regression and Observability Baseline

- Antes de importações/migrações, criar backup timestamped de `data/` e de `data/app.sqlite3` quando existir.
- Node/Express legado deve continuar verificável até paridade formal.
- Cada story deve executar `npm run lint`, `npm run typecheck` e `npm test`.
- Funcionalidades Python devem acrescentar comandos equivalentes de pytest/Ruff/mypy quando o backend existir.
- Toda operação crítica deve ter logs sem segredos, request id ou identificador equivalente, contagens de sucesso/falha e evento de auditoria quando aplicável.

## Risks

| Risk | Mitigation |
|------|------------|
| Introdução Python quebra fluxo MVP | Manter Node legado e JSON intactos até paridade testada |
| Migração parcial gera duplicação | Declarar fonte de verdade por funcionalidade durante coexistência |
| Papéis e permissões crescem cedo demais | Começar com permissões mínimas, escopo explícito e validação no backend |
| Fórmula académica ainda indefinida | Construir engine configurável, não fórmula rígida |
| Publicação fica inconsistente com broadcast | Ligar snapshots a `broadcast_jobs` e `notification_deliveries` |

---

*Epic reconciled by Pax, PO — 2026-05-28*
