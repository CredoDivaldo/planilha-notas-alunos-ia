# Decisões Arquitecturais Resolvidas

1. **Ponto de entrada Python:** o alvo é backend principal em Python, com FastAPI em `backend/app/main.py` e comando local `python -m uvicorn backend.app.main:app --reload --port 8000`.
2. **Base de dados relacional local:** SQLite em `data/app.sqlite3`, com WAL activado em runtime e migrações Alembic versionadas.
3. **Estratégia JSON:** JSON é legado/coexistente. A migração inicial lê JSON para tabelas de staging ou domínio, nunca apaga os ficheiros e mantém o Node intacto até paridade.
4. **Autenticação:** sessões server-side com cookie `HttpOnly`, `SameSite=Lax` ou `Strict` quando possível, palavra-passe com hash Argon2id, rotação de sessão no login e na troca de palavra-passe.
5. **Modelo de palavra-passe inicial:** a arquitectura suporta geração de segredo temporário de uso único, armazenado apenas como hash e marcado com `must_change_password=true`. O canal exacto de entrega fica como decisão de produto.
6. **Publicação:** broadcast explícito cria `publication_snapshots` imutáveis ligados a `broadcast_jobs`; o portal lê apenas a versão publicada actual.
7. **Contrato API:** endpoints novos ficam em `/api/v1`; endpoints legados Node permanecem até substituição validada.
8. **Comandos de qualidade:** manter `npm run lint`, `npm run typecheck`, `npm test` e `npm run quality`; adicionar gates Python equivalentes quando `backend/` existir.
