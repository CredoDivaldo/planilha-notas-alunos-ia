# Coding Standards Handoff

**Status:** standards mínimos para handoff; `docs/architecture.md` é a fonte decisória principal.

## Regras Gerais

- Trabalhar por stories em `docs/stories/`.
- Manter checklist, File List e evidência de quality gates actualizados antes de concluir uma story.
- Não inventar requisitos de produto fora de PRD, arquitectura e stories.
- Preservar fluxo Node legado durante a transição.

## JavaScript Actual

- CommonJS.
- Separação entre rotas, serviços e utilitários.
- Usar tratamento de erro consistente para rotas assíncronas.
- Executar `npm run lint`, `npm run typecheck` e `npm test`.

## Python Alvo

- Type hints em código de aplicação.
- Pydantic para contratos externos.
- SQLAlchemy para persistência.
- Alembic para cada alteração de esquema.
- Imports absolutos a partir de `backend.app`.
- Respostas de erro API com `code`, `message`, `details?` e `request_id?`.

## Segurança e Observabilidade

- Não registar palavras-passe, tokens, `EVOLUTION_API_KEY` ou payloads sensíveis.
- Validar autorização por papel e escopo no backend.
- Criar auditoria para uploads, alterações de notas, publicações, aprovações e envios.
- Incluir request id ou identificador equivalente em operações críticas.
