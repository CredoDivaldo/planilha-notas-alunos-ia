# Source Tree Handoff

**Status:** fonte curta de handoff; `docs/architecture.md` continua a fonte decisória principal.

## Estrutura Actual

```plaintext
src/        Node/Express legado
public/     Frontend estático actual
tests/      Jest/Supertest
data/       JSON legado e futuro SQLite local
docs/       PRD, arquitectura, stories e reviews
```

## Estrutura Alvo para Epic 5

```plaintext
backend/
  app/
    main.py
    core/
    auth/
    academic/
    grades/
    publication/
    notifications/
    portal/
    audit/
  migrations/
  tests/
data/
  app.sqlite3
  legacy-backups/
docs/api/
docs/framework/
pyproject.toml
```

## Regras

- Node legado fica preservado até paridade validada.
- Python não deve depender de módulos JavaScript.
- Node não deve escrever directamente na SQLite sem camada formal de compatibilidade.
- JSON existente não deve ser apagado por migrações.
