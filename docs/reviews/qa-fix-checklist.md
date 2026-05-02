# QA Fix Checklist — P0/P1

Baseado estritamente em `docs/reviews/qa-review.md` (Blocking Findings), sem expansão de escopo.

## P0 — Bloqueios de gate (obrigatórios antes de novo review)

### P0.1 — Script `test` definido e executável
- **Resultado esperado (binário):** PASSA / FALHA  
  PASSA se `npm test` executar a suíte e terminar com exit code 0.
- **Ficheiros alvo:**
  - `package.json`
- **Comando de validação:**
  - `npm test`
- **Evidência mínima aceitável:**
  - Trecho de output com execução de testes e status final de sucesso (exit code 0).

### P0.2 — Script `lint` definido e executável
- **Resultado esperado (binário):** PASSA / FALHA  
  PASSA se `npm run lint` executar e terminar com exit code 0.
- **Ficheiros alvo:**
  - `package.json`
- **Comando de validação:**
  - `npm run lint`
- **Evidência mínima aceitável:**
  - Trecho de output do lint sem erros bloqueantes e exit code 0.

### P0.3 — Script `typecheck` definido e executável (ou equivalente formalmente acordado)
- **Resultado esperado (binário):** PASSA / FALHA  
  PASSA se `npm run typecheck` executar e terminar com exit code 0.
- **Ficheiros alvo:**
  - `package.json`
- **Comando de validação:**
  - `npm run typecheck`
- **Evidência mínima aceitável:**
  - Trecho de output do typecheck (ou equivalente acordado) com exit code 0.

### P0.4 — Cobertura mínima de testes do fluxo crítico do MVP
- **Resultado esperado (binário):** PASSA / FALHA  
  PASSA se a suíte cobrir e validar os 5 cenários exigidos:
  1) upload estudantes, 2) upload notas, 3) geração de match, 4) envio `dryRun`, 5) envio real com falha simulada.
- **Ficheiros alvo:**
  - `tests/` (ou estrutura de testes equivalente já adoptada no projecto)
  - `src/routes/students.js`
  - `src/routes/grades.js`
  - `src/routes/match.js`
  - `src/routes/send.js`
- **Comando de validação:**
  - `npm test`
- **Evidência mínima aceitável:**
  - Output de testes com casos claramente identificáveis para os 5 cenários acima e status final de sucesso (exit code 0).

## P1 — Estabilização técnica obrigatória no gate actual

### P1.1 — Gestão de erro padronizada nas rotas assíncronas críticas
- **Resultado esperado (binário):** PASSA / FALHA  
  PASSA se `students`, `grades` e `match` tiverem tratamento de erro consistente e observável (sem depender apenas de propagação implícita).
- **Ficheiros alvo:**
  - `src/routes/students.js`
  - `src/routes/grades.js`
  - `src/routes/match.js`
  - `src/server.js` (middleware global de erro)
- **Comando de validação:**
  - `grep -nE "try\s*\{|asyncHandler\(" src/routes/students.js src/routes/grades.js src/routes/match.js`
  - `npm test`
- **Evidência mínima aceitável:**
  - Evidência no código de padrão único de captura/encaminhamento de erro nas três rotas críticas.
  - Evidência de teste a provar resposta consistente em cenário de falha (status e payload de erro previsíveis).

## Critério de fecho deste checklist
- Todos os itens **P0** e **P1** em estado **PASSA** com evidência anexável (logs/comandos + referência de ficheiros alterados).
