# Validação PO Master - Brownfield Full-Stack Enhancement

**Data:** 2026-05-28  
**Agente:** Pax, Product Owner  
**Workflow:** `brownfield-fullstack`  
**Step:** `po-validate-artifacts`  
**Modo:** all-at-once, revalidação pós-`po-delegate-fixes`

## Sumário Executivo

O projecto foi revalidado como **brownfield full-stack com componentes UI**. A ronda de correcções removeu os blockers da validação anterior: a Story 5.5 foi criada, as Stories 5.1-5.4 foram reconciliadas com FastAPI, SQLite, Alembic, `/api/v1`, sessões, Argon2id, snapshots, rollback, regressão e observabilidade mínima, e os artefactos antigos de QA/débito foram marcados como históricos quando contradizem os gates actuais.

**Decisão PO:** APPROVED.  
**Prontidão estimada:** 91%  
**Risco de integração:** Médio-alto, esperado para brownfield maior, mas agora mitigado por sequenciação, regressão Node, rollback local e separação de fonte de verdade por fase.  
**Recomendação:** avançar para `po-shard-documents`.

As decisões de produto ainda em aberto permanecem aceitáveis nesta fase porque estão explicitamente isoladas e as stories continuam testáveis sem inventar regras finais.

## Evidência Inspeccionada

- PRD: `docs/prd.md`, `docs/prd/index.md`
- Arquitectura: `docs/architecture.md`, `docs/architecture/index.md`, `docs/architecture/system-architecture.md`
- Frontend: `docs/frontend/frontend-spec.md`
- Epic principal: `docs/stories/epics/epic-5-academic-platform-foundation.md`
- Stories: `docs/stories/5.1.*` a `docs/stories/5.5.*`
- Handoffs: `docs/api/README.md`, `docs/framework/coding-standards.md`, `docs/framework/source-tree.md`, `docs/framework/tech-stack.md`
- QA/reviews/débito: `docs/reviews/qa-review.md`, `docs/prd/technical-debt-DRAFT.md`, `docs/prd/technical-debt-assessment.md`, `docs/reports/TECHNICAL-DEBT-REPORT.md`, `docs/qa/gates/2.1-quality-scripts-baseline.yml`
- Código e manifests para gates: `package.json`, `src/`, `tests/`, `data/`

## Quality Gates Executados

- `npm run lint`: PASS
- `npm run typecheck`: PASS
- `npm test`: PASS
  - `tests/critical-flow.test.js`: 1 suite, 2 testes aprovados

## Checklist PO Master

| Categoria | Estado | Achado principal |
|---|---|---|
| 1. Project Setup & Initialization | PASS | Brownfield detectado, sistema existente analisado e integração preservada por story. `1.1 Project Scaffolding` é N/A por ser greenfield-only. |
| 2. Infrastructure & Deployment | PASS WITH CAVEATS | FastAPI, SQLite, Alembic, execução local e rollback estão definidos. Cloud, CI/CD remoto, canary e blue/green estão correctamente fora de escopo local-first. |
| 3. External Dependencies & Integrations | PASS WITH CAVEATS | Evolution API é preservada como canal WhatsApp; OpenAPI está conscientemente adiado até o backend FastAPI existir. |
| 4. UI/UX Considerations | PASS | Frontend spec cobre fluxo operacional, componentes, estados, responsividade e WCAG 2.2 AA; portal fica fundado pela Story 5.5. |
| 5. User/Agent Responsibility | PASS | Responsabilidades de professor, delegado, estudante e agentes de desenvolvimento estão claras; acções humanas/TBD não foram convertidas em requisitos inventados. |
| 6. Feature Sequencing & Dependencies | PASS | Epic 5 define sequência 5.1 -> 5.2/5.4 -> 5.3 -> 5.5, com dependências explícitas. |
| 7. Risk Management (Brownfield) | PASS | Preservação Node/JSON, rollback local, snapshots, auditoria, regressão e observabilidade mínima aparecem no epic e nas stories. |
| 8. MVP Scope Alignment | PASS | Escopo local-first está contido; fórmula, aprovação do delegado e entrega de palavra-passe ficam como TBD aceites. |
| 9. Documentation & Handoff | PASS | PRD, arquitectura, epic, stories, API placeholder e framework handoffs estão coerentes para sharding. |
| 10. Post-MVP Considerations | PASS WITH CAVEATS | Futuro cloud/analytics/refinamento UX está separado; monitoria mínima incremental já entra nas stories. |

## Decisões TBD Aceites

1. **Fórmula oficial de cálculo académico e estados derivados.**  
   Aceite porque as stories exigem motor configurável, `formula_version` e estados provisórios publicados por snapshot, sem codificar regra institucional final.

2. **Fluxo exacto de aprovação/validação de acções assistidas pelo delegado.**  
   Aceite porque a fundação modela escopo, estados `pending/approved/rejected` e validação obrigatória do professor para acções sensíveis.

3. **Canal e cerimónia exactos para entrega da palavra-passe inicial do estudante.**  
   Aceite porque a arquitectura exige Argon2id, segredo temporário/uso único, `must_change_password=true` e registo sem segredo em claro, deixando o canal configurável.

## Ajustes Feitos Nesta Revalidação

- `docs/architecture.md`: actualizado para reconhecer que a Story 5.5 já existe e que a reconciliação de QA/débito foi tratada como histórica.
- `docs/architecture/index.md`: actualizado para substituir a instrução de criar/reconciliar Story 5.5 por manutenção de alinhamento.
- `docs/reviews/po-master-validation-2026-05-28.md`: substituído por este relatório pós-correcções.

## Riscos Residuais

1. **Execução brownfield continua sensível.** A introdução de Python/SQLite deve manter Node legado verificável até paridade.
2. **OpenAPI ainda não existe como ficheiro estático.** Isto é aceitável antes da Story 5.1; deve ser exportado quando endpoints FastAPI estabilizarem.
3. **Artefactos históricos ainda contêm texto antigo abaixo das notas de reconciliação.** Aceitável porque estão claramente marcados como históricos; não devem ser usados como fonte actual sem nova revisão.

## Recomendação Final

**Status:** APPROVED  
**Próximo passo recomendado:** `po-shard-documents`

Os artefactos estão prontos para sharding documental. Não há must-fix bloqueante antes do próximo passo. Os pontos restantes são decisões de produto isoladas ou melhorias de acompanhamento, não blockers de planeamento.
