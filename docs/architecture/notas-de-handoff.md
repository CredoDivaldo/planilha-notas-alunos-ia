# Notas de Handoff

## Handoff para Story Manager

Use este documento como fonte arquitectural principal para preparar ou validar stories do Epic 5. A primeira story de implementação deve ser a Story 5.1, com escopo limitado a criar o backend Python FastAPI, `pyproject.toml`, SQLite local, Alembic, bootstrap mínimo e documentação de comandos. Preserve o fluxo Node existente e exija verificação de `npm run quality` como regressão brownfield.

A Story 5.5 já existe; mantenha-a dependente de 5.1-5.4 e limitada ao modelo de leitura do portal do estudante.

## Handoff para Desenvolvimento

Não faça big-bang rewrite. Introduza `backend/` em paralelo, implemente DB e auth de forma incremental, e só redireccione UI/fluxos existentes quando houver paridade testada. A fonte de verdade académica nova é SQLite; JSON é legado. O portal do estudante deve consultar exclusivamente snapshots publicados. Toda acção sensível deve validar autorização no backend e criar auditoria.

## Sequência Recomendada

1. Story 5.1: FastAPI, SQLite, Alembic, bootstrap e quality Python.
2. Story 5.2: autenticação, sessões, papéis e matriz de autorização.
3. Story 5.4: contextos académicos do professor e escopo de upload.
4. Story 5.3: notas internas, cálculo inicial e publicação por snapshot.
5. Story 5.5: modelo de leitura do portal e endpoints do estudante.
