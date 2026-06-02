# Technical Debt DRAFT — Consolidação com Correcções Obrigatórias de QA (Sem DB nesta fase)

> **Nota de reconciliação PO — 2026-05-28:** este draft é histórico e anterior à baseline de qualidade actual. As afirmações sobre ausência de `npm test`, `npm run lint` e `npm run typecheck` estão obsoletas. Para o Epic 5, a estratégia de DB também mudou: SQLite local em `data/app.sqlite3` com Alembic foi decidido em `docs/architecture.md`.

## Contexto e Escopo
Este draft consolida os débitos técnicos identificados a partir de:
- `docs/architecture/system-architecture.md`
- `docs/frontend/frontend-spec.md`
- `docs/reviews/qa-review.md`

Conforme o estado actual do projecto, **não há base de dados aplicacional** nesta fase; portanto, débitos de modelação/queries/migrations ficam marcados como **não aplicável por enquanto**.

## Snapshot do Sistema (estado actual)
- MVP monolítico Node.js/Express com frontend estático servido pelo backend.
- Fluxo operativo principal: upload de estudantes → upload de notas → gerar match → conectar Evolution → envio em massa.
- Persistência local por ficheiros JSON na pasta `data/`.
- Integração externa com Evolution API para WhatsApp.

## Evidência QA incorporada
1. `package.json` sem scripts `test`, `lint` e `typecheck` operacionais.
2. Ausência de testes automatizados do fluxo crítico (`*.test.js` / `*.spec.js`).
3. Rotas assíncronas críticas sem padronização de captura de erro (`students`, `grades`, `match`).

## Débitos Consolidados (por domínio)

### 1) Qualidade de Engenharia e Governança Técnica
1. **Ausência de baseline de qualidade automatizada (lint/test/typecheck).**
   - Impacto: regressões passam sem detecção precoce; baixa confiança para evoluções.
   - Evidência: scripts npm sem lint/test/typecheck no diagnóstico arquitectural e no QA gate.

2. **Estratégia de testes automatizados inexistente por domínio funcional.**
   - Impacto: risco elevado de regressões silenciosas no fluxo upload→match→envio.
   - Evidência: QA report sem cobertura mínima de cenários críticos.

3. **Observabilidade insuficiente (logging estruturado/classificação de erros).**
   - Impacto: diagnóstico lento em produção e baixo poder de auditoria operacional.
   - Evidência: tratamento global de erro genérico sem taxonomia clara.

4. **Validação estrutural fraca de entradas em rotas críticas.**
   - Impacto: risco de payloads inconsistentes e falhas tardias no fluxo.
   - Evidência: validação mínima em endpoints de upload e envio.

### 2) Dados e Persistência (sem DB)
5. **Persistência em JSON sem estratégia explícita de concorrência, integridade e recuperação.**
   - Impacto: risco de corrupção/perda de consistência sob acessos concorrentes e operações repetidas.
   - Evidência: escrita directa de ficheiros de estado crítico.

6. **Sem versionamento formal dos artefactos de processamento (uploads/match/resultados).**
   - Impacto: rastreabilidade limitada para auditoria e rollback funcional.
   - Evidência: artefactos “last-*” sem política robusta de histórico e retenção.

### 3) Arquitetura de Aplicação e Acoplamento
7. **Acoplamento directo entre camada HTTP e integração externa (Evolution).**
   - Impacto: baixa testabilidade, complexidade de evolução e fragilidade perante mudanças da API externa.
   - Evidência: rotas de envio chamam cliente externo directamente no fluxo item-a-item.

8. **Tratamento de erro inconsistente em rotas assíncronas críticas.**
   - Impacto: falhas silenciosas e respostas HTTP inconsistentes em Express 4.
   - Evidência: ausência de `try/catch` consistente ou `asyncHandler` central em rotas críticas.

9. **Frontend com alta concentração de responsabilidades num único ficheiro.**
   - Impacto: manutenção difícil, risco elevado de regressão e baixa escalabilidade de UI.
   - Evidência: lógica completa do fluxo operacional concentrada em `public/app.js`.

### 4) UX Operacional, Acessibilidade e Responsividade
10. **Fluxo não guiado por pré-condições de etapa (state gating insuficiente).**
    - Impacto: utilizador pode executar acções fora de sequência, aumentando erro operacional.
    - Evidência: “Gerar match” e “Disparar” sem bloqueios/indicações fortes de prontidão.

11. **Feedback de estado inconsistente e sem semântica robusta.**
    - Impacto: baixa previsibilidade e confiança; ambiguidades de sucesso vs erro.
    - Evidência: mensagens em elementos neutros e sem padrão visual unificado.

12. **Lacunas de acessibilidade (labels, aria-live, fallback de interacção).**
    - Impacto: experiência degradada para tecnologias assistivas e possível não conformidade WCAG AA.
    - Evidência: inputs sem label associado; uso de `alert()` para confirmação crítica.

13. **Estratégia de mobile incompleta para dados de match e acções críticas.**
    - Impacto: queda de usabilidade em operação de campo/dispositivos estreitos.
    - Evidência: tabela sem adaptação completa para cards/fluxo mobile-first.

### 5) Risco de Fluxo Crítico (Upload → Match → Envio)
14. **Perda de contexto operacional em caso de falha durante regeneração de match.**
    - Impacto: utilizador perde referência do estado anterior e aumenta risco de reprocessamento indevido.
    - Evidência: limpeza de tabela antes de confirmação de novo resultado válido.

15. **Pré-validações insuficientes antes do disparo em massa.**
    - Impacto: potencial envio com dados desactualizados/incompletos; risco reputacional e operacional.
    - Evidência: dependência de match prévio não explícita nem bloqueada de forma robusta.

## Plano de Correcção Obrigatória (QA Gate: NEEDS WORK)

### QG-01 — Baseline de Qualidade Automatizada
- **Prioridade:** P0
- **Dependências:** nenhuma
- **Entregáveis mínimos:**
  - `npm run test`
  - `npm run lint`
  - `npm run typecheck` (ou política formal “N/A” se stack JS puro sem TS)
  - script agregador opcional: `npm run quality`
- **Evidência obrigatória:**
  - anexar output dos comandos em `docs/reviews/evidence/quality-baseline.md`
  - registar data/hora da execução e hash curto do commit

### QG-02 — Estratégia de Testes Automatizados por Domínio
- **Prioridade:** P0
- **Dependências:** QG-01
- **Domínios e cenários mínimos:**
  - **Students:** upload válido, CSV inválido, colunas obrigatórias em falta
  - **Grades:** upload válido, payload inconsistente, erro de parsing
  - **Match:** geração com dados válidos, geração sem pré-condições, falha de processamento
  - **Send:** `dryRun` com sucesso, envio real com falha simulada, idempotência básica de reenvio
- **Meta mínima mensurável:**
  - 1 teste automatizado por cenário crítico listado acima
  - pipeline local com 100% de testes críticos a passar
- **Evidência obrigatória:**
  - relatório de execução em `docs/reviews/evidence/test-strategy-report.md`

### QG-03 — Padronização de Erro em Rotas Assíncronas Críticas
- **Prioridade:** P0
- **Dependências:** QG-01
- **Escopo mínimo:**
  - `src/routes/students.js`
  - `src/routes/grades.js`
  - `src/routes/match.js`
  - rotas de envio críticas equivalentes em `src/routes/`
- **Padrão requerido:**
  - `asyncHandler` único (ou padrão equivalente) para capturar rejeições
  - contrato de erro uniforme (`code`, `message`, `details?`, `requestId?`)
  - mapeamento consistente de códigos HTTP por classe de erro
- **Meta mínima mensurável:**
  - 100% das rotas assíncronas críticas sem handlers `async` “soltos”
  - 0 erro não tratado em cenários de falha simulada dos testes críticos
- **Evidência obrigatória:**
  - matriz rota→padrão em `docs/reviews/evidence/async-error-standardization.md`

## Priorização Actualizada (Severidade × Urgência)

### Prioridade P0 (imediato, bloqueia aprovação de QA)
- QG-01: baseline de qualidade automatizada com evidência.
- QG-02: cobertura mínima de testes críticos por domínio.
- QG-03: padronização de tratamento de erro em rotas assíncronas críticas.
- D10/D15: gating explícito do fluxo para impedir operações fora de sequência.
- D12: correcções de acessibilidade essenciais (labels, aria-live, alternativa a `alert()`).

### Prioridade P1 (curto prazo)
- D3: logging estruturado e taxonomia de erro por domínio.
- D7: redução de acoplamento rota ↔ integração externa (camada de orquestração/domínio).
- D11: sistema semântico unificado de mensagens de estado.
- D13: adaptação mobile funcional para visualização de match e acções.

### Prioridade P2 (médio prazo)
- D5/D6: estratégia formal de consistência, histórico e retenção da persistência em ficheiros.
- D9: modularização progressiva do frontend por componentes e estados.
- D14: preservação de contexto visual em reprocessamentos com falha.

## Dependências de Execução (ordem recomendada)
1. **QG-01** (habilita validação automatizada contínua)
2. **QG-02 e QG-03 em paralelo** (com baseline activa)
3. **D10/D15** (guardrails operacionais no fluxo crítico)
4. **D3 e D7** (robustez arquitectural e observabilidade)
5. **P2** (sustentação estrutural e redução de dívida residual)

## Critérios de Aceite Mensuráveis (para subir Gate para APPROVED)
1. `npm run test`, `npm run lint` e `npm run typecheck` (ou equivalente formal acordado) executam sem falhas em ambiente local padrão.
2. Todos os cenários críticos definidos em QG-02 possuem testes automatizados implementados e a passar.
3. Todas as rotas assíncronas críticas adoptam padrão único de tratamento de erro, com contrato de resposta consistente.
4. Evidências documentadas e rastreáveis em `docs/reviews/evidence/` com data/hora e referência de commit.
5. Reexecução de QA confirma ausência de blockers dos itens 1–3.

## Débitos Não Aplicáveis Nesta Fase (DB)
- Modelação relacional, índices, migrações, tuning de queries e RLS: **não aplicável no estado actual**, pois não há base de dados aplicacional detectada.
- Reavaliar este bloco caso o roadmap introduza DB (SQL/NoSQL) na próxima fase.

## Perguntas para Especialistas

### Para @data-engineer (quando DB entrar no roadmap)
1. Qual seria a estratégia de transição mais segura de JSON-file persistence para DB sem interromper o fluxo operativo actual?
2. Que modelo mínimo de dados (entidades e relacionamentos) preserva auditabilidade de uploads, match e envios?
3. Que política de idempotência/versionamento recomenda para evitar reenvios e inconsistências em lotes?
4. Quais métricas e constraints são essenciais para garantir integridade (ex.: telefone normalizado, estado de envio, versão de match)?

### Para @ux-design-expert
5. Qual padrão de progressão guiada (stepper/step cards) melhor equilibra clareza e velocidade para docentes em contexto operacional?
6. Como desenhar feedback de estado (success/warning/error/info) para reduzir interpretação ambígua durante o fluxo crítico?
7. Qual estratégia mobile para “match results” mantém legibilidade e acção rápida sem tabela tradicional?
8. Qual abordagem de confirmação de envio real substitui `alert()` com melhor acessibilidade e menor risco de erro humano?

### Para @qa
9. Que limiar mínimo de cobertura dos testes críticos deve bloquear release (0 falhas nos cenários críticos vs percentagem global)?
10. Que critérios objectivos adicionais devem bloquear release quando houver risco de envio indevido?
11. Como estruturar testes de acessibilidade contínuos (automáticos + manuais) para os estados críticos da UI?

### Para @devops
12. Quais sinais operacionais (logs, métricas, alertas) são obrigatórios para monitorar falhas de integração com Evolution?
13. Qual estratégia de segregação de ambientes (dev/homolog/prod) minimiza risco de disparo real acidental?

## Hipóteses e Assunções (a validar)
- Operação principal continuará single-page no curto prazo.
- A integração Evolution permanecerá como canal principal de envio.
- Não há requisito imediato de multiutilizador concorrente em grande escala (revalidar com stakeholders).

## Próximos Passos Recomendados
1. Converter QG-01, QG-02 e QG-03 em stories accionáveis com owner e prazo.
2. Publicar evidências em `docs/reviews/evidence/` e solicitar nova execução de QA gate.
3. Implementar guardrails de fluxo (D10/D15) imediatamente após estabilizar baseline.
4. Planear lote P1 com foco em observabilidade, desacoplamento e consistência de UX operacional.
