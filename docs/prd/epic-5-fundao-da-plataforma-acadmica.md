# Epic 5: Fundação da Plataforma Académica

**Objectivo do epic:** estabelecer a fundação de plataforma académica com Python, base de dados relacional local, modelo académico, autenticação por papéis, publicação controlada e leitura segura pelo estudante.

**Requisitos de integração:** preservar o fluxo MVP actual até que a fundação nova tenha equivalência validada; tratar JSON como legado/transitório; manter WhatsApp como canal principal; garantir que o portal lê apenas dados publicados.

## Story 5.1 Fundação de Backend Python e Base de Dados Local

Como equipa de desenvolvimento,  
queremos mover a fundação do sistema para um backend Python com base de dados relacional local,  
para que a plataforma académica possa evoluir sobre um modelo de domínio que suporte os novos requisitos de produto.

### Critérios de Aceitação
1. Existe entrypoint FastAPI em `backend/app/main.py` e manifesto de dependências para execução do backend.
2. Existe SQLite em `data/app.sqlite3` com Alembic e bootstrap de esquema inicial.
3. O esquema inicial inclui estudantes, professores, semestres, turnos, turmas, disciplinas, alocações docentes, matrículas e credenciais.
4. JSON é documentado como legado/transitório e não como fonte de verdade.
5. Instruções locais de execução e qualidade são actualizadas.

### Verificação de Integração
1. **IV1:** O fluxo actual de upload, match e envio continua verificável após a introdução da fundação.
2. **IV2:** Dados JSON existentes não são removidos nem reescritos sem plano de migração.
3. **IV3:** Comandos de qualidade existentes continuam a passar.

## Story 5.2 Fundação de Autenticação e Papéis

Como Product Owner,  
quero uma fundação de autenticação e papéis para professor, delegado e estudante,  
para que o acesso às notas e funcionalidades operacionais seja controlado desde o início.

### Critérios de Aceitação
1. O modelo suporta login de estudante por número de estudante e palavra-passe.
2. O primeiro acesso exige troca obrigatória de palavra-passe.
3. Professores têm contas individuais distintas da identidade de estudante.
4. Delegados são modelados como estudantes com permissões técnicas adicionais e escopo limitado.
5. Acções permitidas e bloqueadas por papel ficam documentadas.

### Verificação de Integração
1. **IV1:** O professor mantém controlo exclusivo sobre notas e publicação.
2. **IV2:** O delegado não herda permissões globais de professor.
3. **IV3:** A autorização inicial não expõe notas não publicadas ao estudante.

## Story 5.3 Fundação do Fluxo de Publicação de Notas

Como professor,  
quero que o sistema distinga notas internas de notas publicadas,  
para que os estudantes vejam resultados apenas depois de uma acção explícita de broadcast.

### Critérios de Aceitação
1. O modelo distingue registos internos editáveis de snapshots publicados.
2. Broadcast explícito é o gatilho de publicação.
3. Alterações posteriores suportam novo broadcast.
4. O estudante lê apenas a versão publicada actual.

### Verificação de Integração
1. **IV1:** Notas internas não aparecem no portal.
2. **IV2:** Snapshot publicado fica ligado ao broadcast correspondente.
3. **IV3:** Re-publicação não apaga rastreabilidade operacional.

## Story 5.4 Configuração de Contexto Académico pelo Professor

Como professor,  
quero configurar os meus próprios contextos académicos,  
para poder gerir a turma, disciplina, semestre e turno correctos antes de importar notas ou publicar informação.

### Critérios de Aceitação
1. O sistema modela `turma + disciplina + semestre + turno` como contexto operacional explícito.
2. Um professor pode ter múltiplos contextos activos.
3. A mesma disciplina pode existir em várias turmas/contextos sem colisão.
4. Cada upload fica limitado a um contexto académico específico.

### Verificação de Integração
1. **IV1:** Uploads actuais passam a ter escopo académico claro antes de migração.
2. **IV2:** Contextos de professores diferentes não se misturam.
3. **IV3:** O modelo suporta várias disciplinas por estudante no mesmo semestre.

## Story 5.5 Fundação do Modelo de Leitura do Portal do Estudante

Como estudante,  
quero consultar a minha informação académica publicada num único portal,  
para poder ver notas actuais, estado e calendário sem depender apenas de broadcasts de mensagens.

### Critérios de Aceitação
1. O modelo de leitura do portal usa apenas snapshots publicados.
2. O portal agrega notas publicadas por número de estudante.
3. O portal expõe estado académico actual, turma, curso e calendário publicado.
4. Dados internos, rascunhos e histórico detalhado não são expostos ao estudante.

### Verificação de Integração
1. **IV1:** O portal não lê directamente registos internos de notas.
2. **IV2:** A consulta por número de estudante consolida disciplinas disponíveis.
3. **IV3:** Alterações de calendário só aparecem após publicação correspondente.

**Nota de Backlog:** a Story 5.5 foi criada em `docs/stories/5.5.student-portal-read-model-foundation.md` e deve ser executada depois das fundações de backend, autenticação, contexto académico e publicação.
