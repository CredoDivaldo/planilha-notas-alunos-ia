# Normas de Código e Convenções

## Conformidade com Standards Existentes

**Estilo JS:** CommonJS, separação rota/serviço, `asyncHandler` para rotas assíncronas, mensagens de erro sanitizadas.

**Linting JS:** `npm run lint`.

**Typecheck JS:** `npm run typecheck`.

**Testes JS:** Jest/Supertest em `tests/`.

**Documentação:** Markdown em `docs/`, stories com tarefas, checklist e file list actualizados antes de conclusão.

## Standards Específicos da Melhoria

- **Python:** usar type hints em código de aplicação, Pydantic para contratos externos e SQLAlchemy models/repositories para persistência.
- **Migrações:** toda alteração de esquema deve ter migração Alembic.
- **Configuração:** variáveis obrigatórias devem ser validadas no arranque.
- **Erros API:** resposta uniforme com `code`, `message`, `details?` e `request_id?`.
- **Auditoria:** uploads, alterações de notas, publicações, aprovações do delegado e envios devem criar evento auditável.
- **Autorização:** validar papel e escopo em cada use case, não apenas no frontend.

## Regras Críticas de Integração

- **Compatibilidade API:** não alterar contratos Node existentes sem actualizar testes de regressão.
- **DB:** SQLite é fonte de verdade apenas para funcionalidades já migradas; durante coexistência, documentar claramente qual fluxo lê cada fonte.
- **Erros:** falhas de Evolution devem ser registadas por destinatário e devolvidas como resumo, sem vazar segredo ou payload sensível.
- **Logging:** não registar palavras-passe, tokens, `EVOLUTION_API_KEY` ou mensagens completas quando contiverem dados sensíveis.
