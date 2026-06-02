# Escopo da Melhoria e Estratégia de Integração

## Visão Geral da Melhoria

**Tipo de melhoria:** major enhancement brownfield full-stack.

**Escopo:** introduzir backend Python principal, base de dados relacional local, modelo académico, autenticação, papéis, publicação por snapshot e leitura segura pelo portal do estudante, preservando o MVP Node/Express enquanto a equivalência funcional não estiver validada.

**Impacto de integração:** alto. A mudança toca persistência, backend, contratos API, segurança, UI operacional e modelo de domínio.

## Estratégia de Integração

**Estratégia de código:** adoptar uma migração incremental em paralelo. O backend Python entra como novo núcleo académico em `backend/`, enquanto o backend Node existente permanece como caminho legado do fluxo upload -> match -> Evolution -> bulk send até haver paridade testada.

**Estratégia de base de dados:** SQLite local passa a ser a fonte de verdade académica. Os JSON actuais ficam como artefactos legados e fontes de importação inicial, sem remoção automática.

**Estratégia de API:** manter endpoints Node actuais durante a transição e criar API Python versionada sob `/api/v1`. O contrato formal inicial deve cobrir autenticação, contextos académicos, estudantes, importações, notas internas, publicação, portal e notificações.

**Estratégia de UI:** preservar a página operacional actual como ferramenta MVP; evoluir gradualmente para consumir a API Python quando os fluxos equivalentes estiverem prontos. O portal do estudante deve ser uma área separada, autenticada e limitada a dados publicados.

## Requisitos de Compatibilidade

- **Compatibilidade API existente:** `POST /api/students/upload`, `POST /api/grades/upload`, `POST /api/match/generate`, `GET/POST /api/evolution/*` e `POST /api/send/bulk` devem continuar verificáveis durante a transição.
- **Compatibilidade de dados:** os ficheiros em `data/` não devem ser apagados nem reescritos por migrações sem backup e aprovação explícita.
- **Compatibilidade UI/UX:** o fluxo conceptual de etapas deve manter a sequência upload -> match -> conexão -> envio/publicação.
- **Impacto de performance:** SQLite é suficiente para uso local e turmas académicas em escala moderada; qualquer concorrência real multiutilizador deve reabrir avaliação de DB.
