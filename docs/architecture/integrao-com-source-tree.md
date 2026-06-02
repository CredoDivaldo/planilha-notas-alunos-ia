# Integração com Source Tree

## Estrutura Actual Relevante

```plaintext
.
├── src/
│   ├── app.js
│   ├── server.js
│   ├── routes/
│   ├── services/
│   └── utils/
├── public/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── tests/
│   └── critical-flow.test.js
├── data/
│   ├── students.json
│   ├── grades-last-upload.json
│   └── match-last.json
├── docs/
└── package.json
```

## Nova Organização Prevista

```plaintext
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/
│   │   ├── auth/
│   │   ├── academic/
│   │   ├── grades/
│   │   ├── publication/
│   │   ├── notifications/
│   │   ├── portal/
│   │   └── audit/
│   ├── migrations/
│   └── tests/
├── data/
│   ├── app.sqlite3
│   └── legacy-backups/
├── docs/
│   ├── architecture.md
│   └── api/
├── src/
│   └── ... Node legado preservado durante transição
└── pyproject.toml
```

## Regras de Integração

- **Nomenclatura:** usar nomes de domínio explícitos em inglês nos módulos técnicos e manter terminologia de produto em documentação: estudante, professor, delegado, semestre, turno, turma, disciplina, publicação e broadcast.
- **Importações:** no Python, preferir imports absolutos a partir de `backend.app`.
- **Fronteiras:** Node legado não deve escrever na DB SQLite sem camada de compatibilidade formal. Python não deve depender de módulos JS.
- **Documentação:** qualquer endpoint Python novo deve aparecer na OpenAPI e ser referenciado por story.
