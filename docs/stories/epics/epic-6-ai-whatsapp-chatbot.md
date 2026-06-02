# Epic 6: AI WhatsApp Chatbot

**Epic ID:** EPIC-6  
**Status:** Complete  
**Created:** 2026-05-31  
**Updated:** 2026-06-02  
**Owner:** @pm (Morgan)  
**QA Gate:** PASS (2026-06-02)  

---

## Overview

Adicionar um chatbot com IA ao canal WhatsApp já existente, permitindo que estudantes enviem perguntas em linguagem natural sobre as suas notas publicadas e recebam respostas automáticas geradas por um modelo de linguagem (Claude API ou OpenAI).

Este epic cumpre o requisito externo da disciplina de Fundamentos de Programação: **o projecto deve integrar IA de forma funcional**.

## Business Context

O sistema já notifica estudantes via WhatsApp quando as notas são publicadas (Evolution API). A extensão natural deste canal é permitir que o estudante também **responda** ao número e obtenha informação sobre as suas notas em linguagem natural, sem precisar de aceder ao portal.

O chatbot com IA:
- usa o mesmo canal WhatsApp já configurado;
- responde apenas sobre notas publicadas (respeita FR8/FR9);
- integra um modelo de linguagem real, cumprindo o requisito de IA;
- não requer infraestrutura nova — usa FastAPI (Epic 5) e Evolution API já presentes.

## Scope

### IN
- Webhook Python no FastAPI para receber mensagens WhatsApp da Evolution API.
- Identificação do estudante pelo número de telefone (tabela `students`).
- Serviço de IA em Python que constrói prompt com contexto de notas publicadas do estudante e responde em Português.
- Envio da resposta gerada pelo modelo via Evolution API.
- Recusa educada de perguntas sobre notas não publicadas.
- Rate limiting básico por estudante.
- Endpoint de teste (dry-run) para desenvolvimento.
- Logs de interacções do chatbot.

### OUT
- Histórico de conversas persistido (estado conversacional multi-turno).
- IA fine-tuned ou modelo local.
- Suporte a documentos, imagens ou outros media.
- Integração com outros canais (e-mail, SMS).
- Interface de gestão do chatbot no frontend.

## Success Criteria

| Critério | Métrica |
|----------|---------|
| IA integrada | Modelo de linguagem real chamado via API para gerar respostas |
| WhatsApp funcional | Aluno envia mensagem e recebe resposta automática |
| Isolamento de dados | Chatbot só responde sobre notas publicadas; nunca expõe dados internos |
| Recusa educada | Mensagem clara quando não há notas publicadas ou aluno não identificado |
| Qualidade mantida | `npm run lint`, `npm run typecheck`, `npm test` e `pytest` continuam a passar |

## Dependencies

- **Story 5.1:** FastAPI, SQLite e base de API necessários.
- **Story 5.2:** Modelo de `students` com número de telefone necessário para identificação.
- **Story 5.3:** `publication_snapshots` necessários para aceder a notas publicadas.
- **Story 5.5:** Student read model necessário para construir contexto do chatbot.
- **Evolution API:** já integrada (CR4); precisa de suporte a webhook de entrada.
- **Claude API ou OpenAI:** chave de API em variável de ambiente `AI_API_KEY`.

## Stories

### Story 6.1: WhatsApp Webhook Handler
- **Points:** 3
- **Owner:** @dev
- **Priority:** P0
- **Description:** Criar endpoint FastAPI que recebe mensagens WhatsApp da Evolution API, identifica o estudante pelo número de telefone e encaminha para o serviço de chatbot.
- **File:** `docs/stories/6.1.whatsapp-webhook-handler.md`

### Story 6.2: AI Grade Query Service
- **Points:** 5
- **Owner:** @dev
- **Priority:** P0
- **Description:** Integrar modelo de linguagem (Claude API ou OpenAI), construir prompt com notas publicadas do estudante e gerar resposta em linguagem natural em Português.
- **File:** `docs/stories/6.2.ai-grade-query-service.md`

### Story 6.3: Chatbot End-to-End Flow
- **Points:** 3
- **Owner:** @dev
- **Priority:** P0
- **Description:** Ligar webhook → serviço de IA → resposta WhatsApp, adicionar rate limiting, tratamento de erros e teste end-to-end completo.
- **File:** `docs/stories/6.3.chatbot-end-to-end-flow.md`

## Story Sequencing

```
Story 6.1 (webhook) → Story 6.2 (IA) → Story 6.3 (end-to-end)
```

Stories 6.1 e 6.2 podem ser desenvolvidas em paralelo como design, mas a Story 6.3 depende de ambas implementadas.

## Timeline

- **Sprint 5:** Story 6.1 + Story 6.2 (em paralelo).
- **Sprint 6:** Story 6.3.
- **Effort Total:** 11 pontos.

> Nota: Epic 6 começa após Epic 5 estar suficientemente avançado — mínimo Stories 5.1, 5.2, 5.3 e 5.5 completas.

## Risks

| Risco | Mitigação |
|-------|-----------|
| Chatbot expõe notas não publicadas | Queries ao read model de snapshots publicados apenas; nunca acede a `grade_entries` |
| Chave de API de IA não disponível | Usar variável de ambiente `AI_API_KEY`; endpoint de teste usa mock quando ausente |
| Evolution API não suporta webhook de entrada | Verificar configuração da instância antes de implementar; documentar pré-requisito |
| Aluno não identificado pelo telefone | Resposta educada pedindo contacto com o professor; não expor dados de outros alunos |
| Rate abuse (spam de mensagens) | Rate limiting por número de telefone (max 10 mensagens/dia por defeito) |

---

*Epic criado por Orion, aiox-master — 2026-05-31 (correct-course: requisito de IA)*
