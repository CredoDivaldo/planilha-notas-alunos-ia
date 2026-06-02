# Restrições Técnicas e Requisitos de Integração

## Stack Tecnológico Existente

**Linguagens:** JavaScript actual; Python obrigatório na arquitectura alvo.  
**Frameworks:** Node.js + Express no MVP actual; FastAPI decidido para o backend Python alvo.  
**Base de dados:** JSON local no MVP actual; SQLite local em `data/app.sqlite3` decidido como base relacional alvo.  
**Infraestrutura:** execução local, Docker Compose para Evolution API.  
**Dependências externas:** Evolution API para WhatsApp, `csv-parse`, `multer`, `cors`, `dotenv`, Jest, ESLint e TypeScript checker.

## Abordagem de Integração

**Estratégia de integração de base de dados:** migrar incrementalmente de JSON legado para SQLite com Alembic, backup local e importação auditável.  
**Estratégia de integração de API:** manter endpoints/fluxos actuais durante transição e introduzir endpoints FastAPI sob `/api/v1`, com OpenAPI gerado pelo runtime.  
**Estratégia de integração frontend:** evoluir a UI operacional existente para fluxos guiados e criar portal do estudante quando o modelo de leitura publicado estiver definido.  
**Estratégia de integração de testes:** manter `npm run quality` para a base Node actual e acrescentar comandos equivalentes para Python quando o backend for introduzido.

## Organização de Código e Normas

**Abordagem de estrutura de ficheiros:** respeitar a estrutura existente `src/`, `public/`, `tests/` e acrescentar `backend/app/main.py`, `backend/migrations/` e `pyproject.toml` quando a Story 5.1 for implementada.  
**Convenções de nomenclatura:** manter nomes de domínio explícitos: estudante, professor, delegado, semestre, turno, turma, disciplina, publicação e broadcast.  
**Normas de código:** aplicar padrões existentes do repositório e formalizar documento dedicado antes de expansão substancial.  
**Normas de documentação:** histórias devem actualizar checklist e file list; decisões abertas devem permanecer visíveis em PRD/arquitectura até resolução.

## Implantação e Operações

**Integração do processo de build:** manter comandos actuais e acrescentar comandos Python quando existirem artefactos executáveis.  
**Estratégia de implantação:** local-first nesta fase; infraestrutura cloud, CI/CD remoto, canary e blue/green são N/A/fora de escopo.  
**Monitoria e logging:** auditabilidade operacional deve cobrir uploads, alterações, broadcasts, aprovações e falhas.  
**Gestão de configuração:** variáveis Evolution API continuam necessárias; validação startup e documentação de configuração devem ser formalizadas.

## Avaliação de Riscos e Mitigação

**Riscos técnicos:** duplicação temporária entre Node e Python; migração JSON para SQLite; ausência de OpenAPI exportado até o backend FastAPI existir.  
**Riscos de integração:** inconsistência entre broadcast WhatsApp, snapshot publicado e portal do estudante; Evolution API pode falhar ou gerar envios parciais.  
**Riscos de implantação:** expansão de stack sem comandos de qualidade equivalentes pode reduzir verificabilidade.  
**Estratégias de mitigação:** decidir arquitectura antes de implementação, preservar fluxo actual até substituição validada, introduzir snapshots publicados, manter testes de fluxo crítico, e exigir validação PO antes de mover stories para implementação.
