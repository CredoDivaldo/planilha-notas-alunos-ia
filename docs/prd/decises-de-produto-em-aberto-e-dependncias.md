# Decisões de Produto em Aberto e Dependências

## Decisões de Produto em Aberto
1. Fórmula oficial de cálculo académico e estados derivados.
2. Fluxo exacto de aprovação/validação de acções assistidas pelo delegado.
3. Forma exacta de geração, entrega e segurança da palavra-passe inicial do estudante.

## Decisões de Arquitectura Resolvidas em `docs/architecture.md`
1. Ponto de entrada Python: FastAPI em `backend/app/main.py`.
2. Base de dados relacional local: SQLite em `data/app.sqlite3`.
3. Estratégia de migração: JSON permanece legado/coexistente e fonte de importação auditável, sem remoção automática.
4. Publicação: snapshots imutáveis ligados a `broadcast_jobs`.
5. Autenticação/autorização: sessões server-side, cookie `HttpOnly`, Argon2id, primeira troca obrigatória e papéis com escopo no backend.

## Dependências de Backlog e Validação
1. Executar Story 5.5 apenas depois das dependências 5.1-5.4 ficarem prontas.
2. Reconciliar histórias referenciadas nos Epics 2, 3 e 4 que ainda não têm ficheiros.
3. Actualizar reviews/QA obsoletos: `docs/reviews/qa-review.md` ainda reporta ausência de scripts de qualidade, enquanto `package.json`, Story 2.1 e gate QA indicam PASS.
4. Exportar OpenAPI para `docs/api/openapi.json` quando o backend FastAPI existir.
5. Executar validação formal de PO antes de aprovar qualquer story para implementação.
