# UX Specialist Review — Revalidação de Impacto após mudanças no DRAFT (Fase 6)

## 1) Contexto da Revalidação
Esta revalidação UX/UI foi actualizada com base nos artefactos:
- `docs/frontend/frontend-spec.md`
- `docs/prd/technical-debt-DRAFT.md` (versão consolidada com correcções obrigatórias de QA)
- `docs/reviews/db-specialist-review.md`
- `docs/reviews/qa-review.md`

O DRAFT introduziu uma estrutura mais rigorosa de execução (QG-01/QG-02/QG-03), priorização P0/P1/P2 e critérios de aceite mensuráveis. A tensão central mantém-se: preservar velocidade operacional para docentes sem abrir espaço a erro humano em acções críticas de envio.

## 2) Veredicto UX Revalidado
**Veredicto:** `APPROVED WITH CONCERNS (REVALIDADO)`

**Leitura executiva:**
- Houve melhoria material na **clareza de governação técnica** do plano, sobretudo com dependências e evidências obrigatórias.
- O DRAFT passou a endereçar explicitamente riscos UX críticos (D10, D12, D15), o que reduz ambiguidade de direcção.
- Contudo, os riscos continuam **activos até implementação**; por isso, o veredicto não sobe para aprovação sem ressalvas nesta fase.

## 3) O que mudou no DRAFT e impacto directo em UX

### 3.1 Introdução de QG-01/QG-02/QG-03 com evidência obrigatória
**Mudança no DRAFT:** baseline de qualidade, estratégia de testes críticos e padronização de erro em rotas assíncronas.

**Impacto UX:**
- Melhora a previsibilidade de comportamento do sistema em estados de falha.
- Reduz risco de mensagens inconsistentes e fluxos interrompidos sem retorno claro ao utilizador.
- Cria condições para validar UX operacional em regressões, não apenas em validação manual pontual.

### 3.2 Priorização P0 passou a incluir D10/D15/D12 explicitamente
**Mudança no DRAFT:** state gating, pré-validações antes do disparo e acessibilidade essencial foram elevados a P0.

**Impacto UX:**
- Alinha o plano técnico com os riscos de maior severidade para utilizadores finais.
- Reduz probabilidade de acções fora de sequência e envio indevido.
- Endereça o principal vector de erro operacional identificado na revisão anterior.

### 3.3 Critérios de aceite mensuráveis e rastreáveis
**Mudança no DRAFT:** critérios objectivos para subida de gate, com exigência de evidência em `docs/reviews/evidence/`.

**Impacto UX:**
- Favorece validação auditável de melhorias reais, evitando “falso verde” por percepção subjectiva.
- Suporta decisões de release com base em factos operacionais e não apenas em intenção de correcção.

### 3.4 Sequência de execução explicitada
**Mudança no DRAFT:** ordem recomendada (QG-01 → QG-02/QG-03 → D10/D15 → D3/D7 → P2).

**Impacto UX:**
- Boa base para mitigação progressiva de risco.
- Ponto de atenção: D11 (sistema semântico unificado de mensagens) ficou em P1; pode atrasar consistência cognitiva no curto prazo se D10/D12 forem executados sem camada semântica coesa.

## 4) Estado actualizado dos riscos UX (após revalidação)

### Riscos que diminuíram (por melhoria de direcção)
1. **Ambiguidade de priorização UX** — diminuiu com D10/D12/D15 em P0.
2. **Falta de verificabilidade** — diminuiu com critérios e evidências obrigatórias.

### Riscos que permanecem elevados (até execução efectiva)
1. **Erro operacional por fluxo fora de sequência** — permanece Alto até gating estar em produção.
2. **Acessibilidade insuficiente em interacções críticas** — permanece Alto até substituir `alert()` e completar `labels` + `aria-live`.
3. **Confirmação de envio potencialmente frágil** — permanece Alto até modal acessível com resumo de impacto.
4. **Experiência mobile em dados densos de match** — permanece Médio/Alto até implementação funcional em cards.

## 5) Ajustes recomendados ao plano (para proteger UX no curto prazo)
1. **Antecipar D11 para fronteira P0/P1**, pelo menos para os estados críticos (`success`, `warning`, `error`, `info`) do fluxo upload→match→envio.
2. **Tratar confirmação de envio real como subgate formal de D15**, com validação de foco, leitura por tecnologia assistiva e copy de impacto inequívoca.
3. **Amarrar cenários de QG-02 a critérios UX mínimos**, incluindo: 
   - bloqueio de acções fora de sequência;
   - persistência de contexto em falha de reprocessamento;
   - feedback semântico e annunciation (`aria-live`) nos estados críticos.
4. **Adicionar prova móvel mínima no ciclo P0/P1** para o ecrã de resultados de match (não deixar apenas para lote tardio).

## 6) Gate UX para transição sem ressalvas
Para evoluir de `APPROVED WITH CONCERNS` para aprovação sem ressalvas, validar evidência concreta de:
- [ ] Gating completo por etapa (locked/active/completed/error) nas acções críticas.
- [ ] Confirmação de envio real sem `alert()`, com modal acessível e foco gerido.
- [ ] `labels` associados + `aria-live` funcional em uploads/processamento/envio.
- [ ] Feedback semântico unificado implementado ao menos no fluxo crítico.
- [ ] MatchDataView com comportamento mobile funcional para decisão rápida.
- [ ] Preservação do último estado válido quando a regeneração falhar.

## 7) Conclusão da Revalidação
As mudanças no DRAFT melhoraram significativamente a qualidade do plano de remediaço e elevaram a maturidade de governação técnica. Ainda assim, o impacto positivo em UX permanece potencial enquanto os itens P0 não forem efectivamente implementados e comprovados por evidência. A recomendação é manter o veredicto revalidado com ressalvas e reexecutar revisão UX após fecho dos gates críticos.