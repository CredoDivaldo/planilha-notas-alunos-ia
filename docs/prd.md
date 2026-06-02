# PRD Brownfield de Melhoria Full-Stack - Planilha de Notas de Alunos

## Análise Introdutória do Projecto e Contexto

### Visão Geral do Projecto Existente

#### Fonte de Análise
- Alinhamento direccionado de PRD em ambiente IDE.
- Fontes usadas: `docs/prd/index.md`, `docs/architecture/index.md`, `docs/architecture/system-architecture.md`, `docs/frontend/frontend-spec.md`, `docs/reviews/*.md`, `docs/qa/**/*.yml`, `docs/qa/**/*.md`, `docs/stories/epics/*.md` e `docs/stories/5.*.md`.
- O analista já classificou a mudança como `major_enhancement`; por isso, este documento consolida e alinha o PRD sem executar novo `document-project`.

#### Estado Actual do Projecto
O projecto actual é um MVP local em Node.js/Express com frontend estático. O fluxo operacional existente permite upload de estudantes, upload de notas, geração de correspondência entre estudantes e notas, e envio em massa por WhatsApp através da Evolution API.

A persistência operacional actual usa ficheiros JSON locais. A arquitectura alvo documentada prevê evolução para uma plataforma académica com backend relevante em Python, base de dados relacional local, modelo académico explícito, publicação controlada por broadcast e portal do estudante.

### Análise da Documentação Disponível

#### Documentação Disponível
- [x] Documentação de stack técnico: presente de forma parcial em `docs/architecture/system-architecture.md`.
- [x] Source tree/arquitectura: presente em `docs/architecture/index.md` e `docs/architecture/system-architecture.md`.
- [x] Normas de código: existe handoff mínimo em `docs/framework/coding-standards.md`; `docs/architecture.md` permanece fonte decisória principal até implementação.
- [x] Documentação de API: existe placeholder controlado em `docs/api/README.md`; OpenAPI será exportado quando o backend FastAPI existir.
- [ ] Documentação de API externa: integração Evolution API documentada por uso e variáveis, mas sem contrato formal.
- [x] Directrizes UX/UI: presente em `docs/frontend/frontend-spec.md`.
- [x] Documentação de dívida técnica: presente em `docs/prd/technical-debt-assessment.md`, `docs/prd/technical-debt-DRAFT.md`, `docs/reports/TECHNICAL-DEBT-REPORT.md` e reviews.
- [x] Outros: epics e stories em `docs/stories/`.

### Definição do Escopo da Melhoria

#### Tipo de Melhoria
- [x] Adição de nova funcionalidade
- [x] Modificação maior de funcionalidade
- [x] Integração com novos sistemas
- [x] Actualização de stack tecnológico
- [x] Correcção de estabilidade e bugs
- [x] Revisão UI/UX
- [ ] Melhorias de performance/escalabilidade
- [ ] Outro

#### Descrição da Melhoria
Transformar o MVP de upload, match e envio WhatsApp numa plataforma académica para gestão, cálculo, publicação e consulta de notas. A evolução deve introduzir domínio académico explícito, autenticação, papéis diferenciados, persistência relacional, publicação controlada e portal do estudante, preservando o fluxo crítico existente durante a transição.

#### Avaliação de Impacto
- [ ] Impacto mínimo
- [ ] Impacto moderado
- [x] Impacto significativo
- [x] Impacto maior

### Objectivos e Contexto de Fundo

#### Objectivos
- Permitir gestão de semestres, turnos, turmas, disciplinas, professores e estudantes.
- Substituir ficheiros JSON como fonte de verdade por uma base de dados real.
- Usar Python como parte central e relevante da solução.
- Separar notas internas de notas publicadas aos estudantes.
- Publicar notas e calendário apenas após acção explícita de broadcast.
- Disponibilizar portal do estudante com autenticação por número de estudante e palavra-passe.
- Modelar professor, delegado e estudante com limites claros de permissão.
- Manter o fluxo crítico actual verificável durante a transição.

#### Contexto de Fundo
O fluxo actual resolve um problema operacional imediato: importar notas e enviar mensagens por WhatsApp. Porém, a evolução do produto exige consolidação académica por estudante, vários contextos de ensino, cálculo configurável, permissões, consulta autónoma pelo estudante e rastreabilidade das publicações.

Sem esta fundação, novas melhorias de frontend, testes ou comunicação continuarão dependentes de um modelo de dados insuficiente para o produto académico pretendido.

### Registo de Alterações

| Alteração | Data | Versão | Descrição | Autor |
|---|---:|---:|---|---|
| PRD formal brownfield criado | 2026-05-27 | 1.0 | Consolidação monolítica do PRD a partir dos artefactos existentes, com decisões em aberto explicitadas | Morgan, PM |

## Requisitos

### Funcionais

1. **FR1:** O sistema deve preservar o fluxo crítico existente de upload de estudantes, upload de notas, geração de match e envio WhatsApp até existir substituição validada.
2. **FR2:** O sistema deve permitir configurar e gerir semestres, turmas, turnos, disciplinas, cursos e relações entre estes elementos.
3. **FR3:** O sistema deve permitir ao professor configurar múltiplos contextos próprios no formato `turma + disciplina + semestre + turno`.
4. **FR4:** O sistema deve permitir cadastrar estudantes, actualizar contactos e associá-los aos contextos académicos relevantes através do número de estudante.
5. **FR5:** O sistema deve permitir importar notas por ficheiros estruturados para uma disciplina de uma turma num semestre específico.
6. **FR6:** O sistema deve permitir corrigir e completar manualmente notas e componentes de avaliação.
7. **FR7:** O sistema deve calcular resultados académicos com base numa fórmula institucional configurável; a fórmula oficial permanece pendente de validação.
8. **FR8:** O sistema deve distinguir dados internos lançados de dados publicados aos estudantes.
9. **FR9:** O sistema deve tornar notas visíveis no portal apenas após broadcast explícito.
10. **FR10:** O sistema deve permitir novo broadcast quando notas ou datas publicadas forem alteradas.
11. **FR11:** O sistema deve permitir broadcast por WhatsApp como canal principal e e-mail como canal complementar quando disponível.
12. **FR12:** O sistema deve permitir ao estudante consultar notas publicadas, estado académico actual, turma, curso e calendário de provas, exames e recursos.
13. **FR13:** O sistema deve suportar login do estudante por número de estudante e palavra-passe, com troca obrigatória no primeiro acesso.
14. **FR14:** O sistema deve permitir perfil de delegado com permissões técnicas limitadas à sua turma.
15. **FR15:** O sistema deve impedir que delegados modifiquem notas directamente, removam turmas ou executem acções sensíveis sem validação do professor.
16. **FR16:** O sistema deve registar uploads, alterações, broadcasts, aprovações e operações sensíveis para auditabilidade operacional.

### Não Funcionais

1. **NFR1:** A persistência académica alvo deve usar base de dados relacional como fonte de verdade, substituindo JSON como persistência primária.
2. **NFR2:** Python deve ser usado de forma central na solução, preferencialmente no backend principal; uma alternativa aceitável é motor académico/importação/cálculo em Python durante uma transição controlada.
3. **NFR3:** O sistema deve proteger acesso a notas e operações administrativas por autenticação e autorização adequadas aos papéis.
4. **NFR4:** O modelo deve suportar evolução futura de fórmulas, componentes de avaliação e regras institucionais sem reescrita estrutural.
5. **NFR5:** O sistema deve manter qualidade verificável por `npm run lint`, `npm run typecheck`, `npm test` e comandos equivalentes que forem introduzidos para Python.
6. **NFR6:** As interfaces novas ou alteradas devem seguir os requisitos de acessibilidade WCAG 2.2 AA definidos no frontend spec.
7. **NFR7:** Operações críticas devem ter feedback claro, estados de erro consistentes e prevenção de acções fora de sequência.
8. **NFR8:** O portal do estudante deve exibir apenas a versão publicada actual, sem expor histórico detalhado de alterações.

### Requisitos de Compatibilidade

1. **CR1:** As capacidades actuais de importação CSV, match e envio WhatsApp não devem ser quebradas sem substituição funcional e validação explícita.
2. **CR2:** Ficheiros JSON existentes podem ser usados como legado, artefacto transitório ou fonte de migração, mas não devem permanecer como fonte de verdade académica alvo.
3. **CR3:** A experiência operacional do professor deve manter a sequência conceptual upload -> match -> envio/publicação durante a transição.
4. **CR4:** A integração com Evolution API deve continuar suportada enquanto o WhatsApp for o canal principal de broadcast.
5. **CR5:** A publicação para portal e notificações deve permanecer dependente de acção humana explícita, sem automação silenciosa.

## Objectivos de Melhoria da Interface

### Integração com a UI Existente
A UI actual é uma página única operacional com cinco etapas. A evolução deve manter clareza de sequência e baixo atrito para docentes, introduzindo gradualmente estados `locked`, `active`, `completed` e `error`, feedback semântico e confirmação acessível para envio real.

### Ecrãs e Vistas Novos ou Alterados
- Painel operacional do professor.
- Vista técnica reduzida do delegado.
- Portal do estudante.
- Gestão de contextos académicos.
- Gestão de notas e componentes de avaliação.
- Calendário de provas, exames e recursos.
- Fluxo de publicação/broadcast.

### Requisitos de Consistência UI
- Usar os princípios de `docs/frontend/frontend-spec.md` para StepCards, StatusMessage, Button e MatchDataView.
- Garantir labels, `aria-live`, foco visível, navegação por teclado e contraste AA.
- Bloquear acções críticas quando pré-condições não estiverem cumpridas.
- Preservar contexto válido anterior quando uma nova operação falhar.

## Restrições Técnicas e Requisitos de Integração

### Stack Tecnológico Existente

**Linguagens:** JavaScript actual; Python obrigatório na arquitectura alvo.  
**Frameworks:** Node.js + Express no MVP actual; FastAPI decidido para o backend Python alvo.  
**Base de dados:** JSON local no MVP actual; SQLite local em `data/app.sqlite3` decidido como base relacional alvo.  
**Infraestrutura:** execução local, Docker Compose para Evolution API.  
**Dependências externas:** Evolution API para WhatsApp, `csv-parse`, `multer`, `cors`, `dotenv`, Jest, ESLint e TypeScript checker.

### Abordagem de Integração

**Estratégia de integração de base de dados:** migrar incrementalmente de JSON legado para SQLite com Alembic, backup local e importação auditável.  
**Estratégia de integração de API:** manter endpoints/fluxos actuais durante transição e introduzir endpoints FastAPI sob `/api/v1`, com OpenAPI gerado pelo runtime.  
**Estratégia de integração frontend:** evoluir a UI operacional existente para fluxos guiados e criar portal do estudante quando o modelo de leitura publicado estiver definido.  
**Estratégia de integração de testes:** manter `npm run quality` para a base Node actual e acrescentar comandos equivalentes para Python quando o backend for introduzido.

### Organização de Código e Normas

**Abordagem de estrutura de ficheiros:** respeitar a estrutura existente `src/`, `public/`, `tests/` e acrescentar `backend/app/main.py`, `backend/migrations/` e `pyproject.toml` quando a Story 5.1 for implementada.  
**Convenções de nomenclatura:** manter nomes de domínio explícitos: estudante, professor, delegado, semestre, turno, turma, disciplina, publicação e broadcast.  
**Normas de código:** aplicar padrões existentes do repositório e formalizar documento dedicado antes de expansão substancial.  
**Normas de documentação:** histórias devem actualizar checklist e file list; decisões abertas devem permanecer visíveis em PRD/arquitectura até resolução.

### Implantação e Operações

**Integração do processo de build:** manter comandos actuais e acrescentar comandos Python quando existirem artefactos executáveis.  
**Estratégia de implantação:** local-first nesta fase; infraestrutura cloud, CI/CD remoto, canary e blue/green são N/A/fora de escopo.  
**Monitoria e logging:** auditabilidade operacional deve cobrir uploads, alterações, broadcasts, aprovações e falhas.  
**Gestão de configuração:** variáveis Evolution API continuam necessárias; validação startup e documentação de configuração devem ser formalizadas.

### Avaliação de Riscos e Mitigação

**Riscos técnicos:** duplicação temporária entre Node e Python; migração JSON para SQLite; ausência de OpenAPI exportado até o backend FastAPI existir.  
**Riscos de integração:** inconsistência entre broadcast WhatsApp, snapshot publicado e portal do estudante; Evolution API pode falhar ou gerar envios parciais.  
**Riscos de implantação:** expansão de stack sem comandos de qualidade equivalentes pode reduzir verificabilidade.  
**Estratégias de mitigação:** decidir arquitectura antes de implementação, preservar fluxo actual até substituição validada, introduzir snapshots publicados, manter testes de fluxo crítico, e exigir validação PO antes de mover stories para implementação.

## Estrutura de Epics e Stories

### Abordagem de Epics

**Decisão de estrutura de epics:** manter múltiplos epics existentes porque o repositório já contém backlog brownfield separado por fundação de qualidade, segurança, UX e fundação académica. Para a melhoria maior actual, o epic principal é o **Epic 5: Academic Platform Foundation**; Epics 2, 3 e 4 permanecem como backlog de remediação e suporte, sujeitos a reconciliação antes de execução.

## Epic 5: Fundação da Plataforma Académica

**Objectivo do epic:** estabelecer a fundação de plataforma académica com Python, base de dados relacional local, modelo académico, autenticação por papéis, publicação controlada e leitura segura pelo estudante.

**Requisitos de integração:** preservar o fluxo MVP actual até que a fundação nova tenha equivalência validada; tratar JSON como legado/transitório; manter WhatsApp como canal principal; garantir que o portal lê apenas dados publicados.

### Story 5.1 Fundação de Backend Python e Base de Dados Local

Como equipa de desenvolvimento,  
queremos mover a fundação do sistema para um backend Python com base de dados relacional local,  
para que a plataforma académica possa evoluir sobre um modelo de domínio que suporte os novos requisitos de produto.

#### Critérios de Aceitação
1. Existe entrypoint FastAPI em `backend/app/main.py` e manifesto de dependências para execução do backend.
2. Existe SQLite em `data/app.sqlite3` com Alembic e bootstrap de esquema inicial.
3. O esquema inicial inclui estudantes, professores, semestres, turnos, turmas, disciplinas, alocações docentes, matrículas e credenciais.
4. JSON é documentado como legado/transitório e não como fonte de verdade.
5. Instruções locais de execução e qualidade são actualizadas.

#### Verificação de Integração
1. **IV1:** O fluxo actual de upload, match e envio continua verificável após a introdução da fundação.
2. **IV2:** Dados JSON existentes não são removidos nem reescritos sem plano de migração.
3. **IV3:** Comandos de qualidade existentes continuam a passar.

### Story 5.2 Fundação de Autenticação e Papéis

Como Product Owner,  
quero uma fundação de autenticação e papéis para professor, delegado e estudante,  
para que o acesso às notas e funcionalidades operacionais seja controlado desde o início.

#### Critérios de Aceitação
1. O modelo suporta login de estudante por número de estudante e palavra-passe.
2. O primeiro acesso exige troca obrigatória de palavra-passe.
3. Professores têm contas individuais distintas da identidade de estudante.
4. Delegados são modelados como estudantes com permissões técnicas adicionais e escopo limitado.
5. Acções permitidas e bloqueadas por papel ficam documentadas.

#### Verificação de Integração
1. **IV1:** O professor mantém controlo exclusivo sobre notas e publicação.
2. **IV2:** O delegado não herda permissões globais de professor.
3. **IV3:** A autorização inicial não expõe notas não publicadas ao estudante.

### Story 5.3 Fundação do Fluxo de Publicação de Notas

Como professor,  
quero que o sistema distinga notas internas de notas publicadas,  
para que os estudantes vejam resultados apenas depois de uma acção explícita de broadcast.

#### Critérios de Aceitação
1. O modelo distingue registos internos editáveis de snapshots publicados.
2. Broadcast explícito é o gatilho de publicação.
3. Alterações posteriores suportam novo broadcast.
4. O estudante lê apenas a versão publicada actual.

#### Verificação de Integração
1. **IV1:** Notas internas não aparecem no portal.
2. **IV2:** Snapshot publicado fica ligado ao broadcast correspondente.
3. **IV3:** Re-publicação não apaga rastreabilidade operacional.

### Story 5.4 Configuração de Contexto Académico pelo Professor

Como professor,  
quero configurar os meus próprios contextos académicos,  
para poder gerir a turma, disciplina, semestre e turno correctos antes de importar notas ou publicar informação.

#### Critérios de Aceitação
1. O sistema modela `turma + disciplina + semestre + turno` como contexto operacional explícito.
2. Um professor pode ter múltiplos contextos activos.
3. A mesma disciplina pode existir em várias turmas/contextos sem colisão.
4. Cada upload fica limitado a um contexto académico específico.

#### Verificação de Integração
1. **IV1:** Uploads actuais passam a ter escopo académico claro antes de migração.
2. **IV2:** Contextos de professores diferentes não se misturam.
3. **IV3:** O modelo suporta várias disciplinas por estudante no mesmo semestre.

### Story 5.5 Fundação do Modelo de Leitura do Portal do Estudante

Como estudante,  
quero consultar a minha informação académica publicada num único portal,  
para poder ver notas actuais, estado e calendário sem depender apenas de broadcasts de mensagens.

#### Critérios de Aceitação
1. O modelo de leitura do portal usa apenas snapshots publicados.
2. O portal agrega notas publicadas por número de estudante.
3. O portal expõe estado académico actual, turma, curso e calendário publicado.
4. Dados internos, rascunhos e histórico detalhado não são expostos ao estudante.

#### Verificação de Integração
1. **IV1:** O portal não lê directamente registos internos de notas.
2. **IV2:** A consulta por número de estudante consolida disciplinas disponíveis.
3. **IV3:** Alterações de calendário só aparecem após publicação correspondente.

**Nota de Backlog:** a Story 5.5 foi criada em `docs/stories/5.5.student-portal-read-model-foundation.md` e deve ser executada depois das fundações de backend, autenticação, contexto académico e publicação.

## Decisões de Produto em Aberto e Dependências

### Decisões de Produto em Aberto
1. Fórmula oficial de cálculo académico e estados derivados.
2. Fluxo exacto de aprovação/validação de acções assistidas pelo delegado.
3. Forma exacta de geração, entrega e segurança da palavra-passe inicial do estudante.

### Decisões de Arquitectura Resolvidas em `docs/architecture.md`
1. Ponto de entrada Python: FastAPI em `backend/app/main.py`.
2. Base de dados relacional local: SQLite em `data/app.sqlite3`.
3. Estratégia de migração: JSON permanece legado/coexistente e fonte de importação auditável, sem remoção automática.
4. Publicação: snapshots imutáveis ligados a `broadcast_jobs`.
5. Autenticação/autorização: sessões server-side, cookie `HttpOnly`, Argon2id, primeira troca obrigatória e papéis com escopo no backend.

### Dependências de Backlog e Validação
1. Executar Story 5.5 apenas depois das dependências 5.1-5.4 ficarem prontas.
2. Reconciliar histórias referenciadas nos Epics 2, 3 e 4 que ainda não têm ficheiros.
3. Actualizar reviews/QA obsoletos: `docs/reviews/qa-review.md` ainda reporta ausência de scripts de qualidade, enquanto `package.json`, Story 2.1 e gate QA indicam PASS.
4. Exportar OpenAPI para `docs/api/openapi.json` quando o backend FastAPI existir.
5. Executar validação formal de PO antes de aprovar qualquer story para implementação.

## Fora de Escopo Nesta Fase de Melhoria
- Gestão financeira.
- Histórico detalhado de alterações visível ao estudante.
- Login do estudante por e-mail.
- Automação de publicação sem acção humana.
- Calendário para actividades fora de provas, exames e recursos.
- Infraestrutura cloud.
- CI/CD remoto, canary, blue/green e produção multiambiente nesta fase local-first.
- Analytics e relatórios avançados.

## Métricas de Sucesso
- Professor consegue configurar contextos académicos e lançar notas com baixo atrito.
- Estudante consegue consultar, num único portal, as notas publicadas de todas as disciplinas disponíveis.
- Sistema publica resultados por WhatsApp e disponibiliza a versão publicada no portal.
- Modelo suporta semestre, turma, turno, disciplina, estudante, professor, delegado e snapshot publicado.
- Python existe de forma explícita e relevante na implementação.
- Comandos de qualidade passam antes de promoção de stories.
