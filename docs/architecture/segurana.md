# Segurança

## Estado Actual

- **Autenticação:** inexistente no MVP Node.
- **Autorização:** inexistente nas rotas actuais.
- **Protecção de dados:** configuração sensível em `.env`; dados académicos persistem em JSON local.
- **Ferramentas:** sem ferramenta de segurança formal detectada.

## Modelo de Segurança Alvo

- **Professor:** conta própria, pode gerir contextos próprios, notas, calendário, publicação e validação de acções sensíveis.
- **Delegado:** autentica como estudante e recebe atribuição técnica limitada a uma turma/contexto; não altera notas directamente, não remove turmas e não publica sem validação quando a acção for sensível.
- **Estudante:** consulta apenas snapshots publicados ligados ao seu número de estudante.
- **Sessão:** cookie `HttpOnly`; expiração curta/moderada em uso local; rotação no login e na troca de palavra-passe.
- **Palavras-passe:** Argon2id; temporárias de uso único; `must_change_password=true` no primeiro acesso.
- **CSRF:** necessário para formulários/browser sessions mutáveis quando a UI consumir API Python por cookie.
- **Rate limiting:** obrigatório nos endpoints de login e broadcast.
- **Segredos:** nunca armazenar palavra-passe inicial em claro; nunca devolver API keys ou segredos no frontend.

## Testes de Segurança

- Testar login inválido, sessão expirada e troca obrigatória de palavra-passe.
- Testar que estudante não acede notas internas nem dados de outro estudante.
- Testar que delegado não edita notas nem executa acções fora do seu escopo.
- Testar que professor não acede contextos de outro professor sem autorização.
- Testar que endpoints de broadcast exigem confirmação explícita e permitem `dry_run`.
