# Introdução

Este documento define a arquitectura formal brownfield para evoluir o MVP local de upload, match e envio WhatsApp para uma plataforma académica com backend principal em Python, base de dados relacional local, autenticação por papéis, publicação controlada e portal do estudante.

O objectivo é orientar desenvolvimento assistido por IA sem quebrar o fluxo MVP já existente: upload de estudantes, upload de notas, geração de match, ligação Evolution, envio em massa e modo `dryRun`.

**Relação com a arquitectura existente:** este documento passa a ser o artefacto decisório principal para o Epic 5. Os documentos `docs/architecture/index.md` e `docs/architecture/system-architecture.md` continuam válidos como contexto, inventário histórico e visão resumida, mas decisões técnicas novas devem seguir este ficheiro quando houver divergência.

## Análise do Projecto Existente

### Estado Actual do Projecto

- **Finalidade principal:** MVP local para importar estudantes e notas por CSV, gerar correspondência e enviar mensagens WhatsApp por Evolution API.
- **Stack actual:** Node.js, Express 4, JavaScript CommonJS, frontend estático em `public/`, Jest, Supertest, ESLint flat config e TypeScript checker por `tsc --noEmit`.
- **Estilo de arquitectura:** monólito local com separação simples entre rotas (`src/routes`), serviços (`src/services`) e UI estática (`public`).
- **Persistência actual:** ficheiros JSON em `data/`, nomeadamente `students.json`, `grades-last-upload.json` e `match-last.json`.
- **Integração externa actual:** Evolution API via HTTP, configurada por `EVOLUTION_BASE_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE` e `EVOLUTION_INTEGRATION`.
- **Execução actual:** `npm run dev` ou `npm start`; Docker Compose apenas para Evolution API.

### Documentação Disponível

- `docs/prd.md` e `docs/prd/index.md` definem a melhoria maior e os requisitos do Epic 5.
- `docs/architecture/index.md` e `docs/architecture/system-architecture.md` registam visão alvo, módulos lógicos e avaliação histórica.
- `docs/frontend/frontend-spec.md` define fluxos, componentes e requisitos WCAG 2.2 AA para a UI operacional.
- `docs/stories/epics/epic-5-academic-platform-foundation.md` define o epic principal de fundação académica.
- `docs/stories/5.1.*` a `docs/stories/5.5.*` existem e cobrem a fundação académica, autenticação, contextos, publicação e modelo de leitura do portal.
- `docs/qa/gates/2.1-quality-scripts-baseline.yml` indica PASS para baseline de qualidade, enquanto alguns reviews antigos ainda reportam ausência desses scripts.

### Restrições Identificadas

- O fluxo operacional actual não pode ser quebrado sem substituição funcional validada.
- JSON pode coexistir temporariamente, mas não deve ser fonte de verdade académica alvo.
- Python deve ser parte central da solução, não apenas utilitário periférico.
- A solução continua local-first; cloud e produção multiambiente estão fora de escopo nesta fase.
- WhatsApp via Evolution API permanece canal principal de broadcast.
- A publicação no portal deve depender de acção humana explícita de broadcast.
- A fórmula académica oficial, o detalhe operacional de aprovação do delegado e a entrega exacta da palavra-passe inicial continuam decisões de produto abertas.

## Epic 6: AI WhatsApp Chatbot

Em 2026-05-31, um requisito externo (a disciplina de Fundamentos de Programação exige integração de IA) determinou a adição do **Epic 6: AI WhatsApp Chatbot**. Esta funcionalidade é aditiva — não altera o Epic 5 nem quebra fluxos existentes.

O chatbot permite ao estudante enviar mensagens para o número WhatsApp da plataforma e receber respostas em linguagem natural sobre as suas notas **publicadas**, usando um modelo de linguagem (Claude API ou OpenAI). O fluxo integra a Evolution API (já presente) com um serviço Python dedicado no backend FastAPI.

**Dependência arquitectural:** o Epic 6 depende das Stories 5.3 (publication snapshots) e 5.5 (student read model) para aceder a dados de notas publicadas. Nenhuma nota interna ou não publicada é exposta pelo chatbot.

Consulte `docs/stories/epics/epic-6-ai-whatsapp-chatbot.md` para detalhes e `docs/architecture/estratgia-de-api-e-integrao.md` para os endpoints.

## Registo de Alterações

| Alteração | Data | Versão | Descrição | Autor |
|---|---:|---:|---|---|
| Arquitectura brownfield formal criada | 2026-05-28 | 1.0 | Consolida decisões técnicas para Python, SQLite, migração JSON, autenticação, publicação e API | Aria, Architect |
| Epic 6 adicionado — AI WhatsApp Chatbot | 2026-05-31 | 1.1 | Requisito externo de IA: chatbot WhatsApp com modelo de linguagem, webhook Evolution API e serviço Python dedicado | Orion, aiox-master |
