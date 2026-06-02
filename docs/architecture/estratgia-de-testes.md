# Estratégia de Testes

## Integração com Testes Existentes

**Framework actual:** Jest + Supertest.

**Organização actual:** `tests/critical-flow.test.js`.

**Cobertura obrigatória existente:** upload de estudantes, upload de notas, match, envio `dryRun` e envio real com falha simulada.

## Novos Testes Python

### Unitários

- **Framework:** pytest.
- **Localização:** `backend/tests/unit/`.
- **Cobertura mínima:** validação de schemas, cálculo académico, autorização por papel, geração de snapshots, adapter Evolution isolado.

### Integração

- **Framework:** pytest com DB SQLite temporário.
- **Localização:** `backend/tests/integration/`.
- **Escopo:** migrações, bootstrap, importação JSON/CSV, login, criação de contexto, publicação, leitura do portal.

### Regressão Brownfield

- **Escopo:** garantir que `npm run quality` continua a passar após introdução Python.
- **Verificação:** fluxo MVP Node deve permanecer verde até ser formalmente substituído.

## Comandos de Qualidade

Comandos actuais obrigatórios:

```bash
npm run lint
npm run typecheck
npm test
npm run quality
```

Comandos Python a introduzir com o backend:

```bash
python -m pytest backend/tests
python -m ruff check backend
python -m mypy backend
python -m alembic upgrade head
```

Quando `pyproject.toml` existir, deve haver agregador documentado, por exemplo `npm run quality:python` ou `make quality-python`, mas a escolha exacta do agregador pode ser feita na Story 5.1.
