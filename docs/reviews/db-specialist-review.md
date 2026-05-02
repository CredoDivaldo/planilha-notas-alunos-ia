# DB Specialist Review  Revalidação de Impacto do DRAFT (Fase 5)

## 1) Contexto da Revalidação
Esta revalidação foi executada sobre:
- `docs/prd/technical-debt-DRAFT.md` (versão actual)
- `docs/architecture/system-architecture.md`

O DRAFT actualizado explicita que **não há base de dados aplicacional nesta fase** e classifica modelação relacional, migrações, índices, tuning e RLS como **não aplicáveis por enquanto**.

## 2) Mudanças Relevantes Detectadas no DRAFT
1. Reclassificação formal de débitos de DB para **N/A nesta fase**.
2. Foco operacional deslocado para:
   - baseline de qualidade (test/lint/typecheck),
   - cobertura de testes críticos,
   - padronização de erro em rotas assíncronas,
   - guardrails do fluxo upload → match → envio.
3. Persistência em JSON continua no centro do risco técnico (concorrência, consistência, recuperação e rastreabilidade).

## 3) Impacto Técnico das Mudanças (Database Lens)

### 3.1 Impacto positivo
- O DRAFT ficou mais consistente com o estado real do sistema (MVP sem DB).
- A priorização P0 foi corrigida para atacar fragilidades imediatas de engenharia e operação, reduzindo risco de regressão funcional no curto prazo.
- A separação “o que corrigir agora” vs “o que preparar para quando houver DB” melhora a governança de execução.

### 3.2 Impacto residual (ainda crítico, mesmo sem DB)
- Persistência em JSON mantém ausência de garantias ACID e trilha formal de evolução.
- Idempotência e auditabilidade do envio continuam como risco alto se não forem formalizadas ao nível de artefactos e regras operacionais.
- Sem contrato canónico de dados versionado, a futura migração JSON → DB tende a custar mais e carregar ambiguidades.

## 4) Veredicto Técnico Actualizado
**Veredicto:** `APPROVED WITH CONSTRAINTS (DB-DEFERRED)`

**Leitura do veredicto:**
- **Aprovado** para o enquadramento de fase actual (sem DB), porque o DRAFT alinhou escopo, prioridades e evidências.
- **Com restrições**, porque os riscos estruturais de dados permanecem e devem ser tratados com guardrails explícitos até à introdução de DB.

## 5) Recomendações Imediatas (sem introduzir DB nesta fase)
1. Formalizar contrato de artefactos JSON críticos (`students`, `grades`, `match`, `send`) com versionamento e validação de schema no write-path.
2. Implementar idempotência mínima persistida por lote/destinatário para evitar reenvio indevido em retries.
3. Registar trilha de auditoria operacional mínima (quem, quando, o quê, resultado, motivo de falha).
4. Definir política de retenção e rotação de ficheiros operacionais e evidências.
5. Adicionar reconciliação periódica simples (contagens/checksums) para detectar deriva/corrupção de estado.

## 6) Gate de Entrada para DB (quando roadmap activar)
A transição para DB deve iniciar quando pelo menos uma destas condições ocorrer:
- exigência de multiutilizador concorrente real,
- necessidade de auditoria/compliance formal,
- aumento de volume/lotes com degradação operacional,
- incidência recorrente de inconsistência/reenvio.

Ao activar esse gate, executar primeiro:
1. Modelo de dados canónico v1 (entidades e chaves);
2. Plano de migração JSON → DB com rollback testado;
3. Estratégia de idempotência e estados de envio como contrato de dados.

## 7) Conclusão
As mudanças no DRAFT foram **adequadas e melhoraram a precisão de escopo** para a fase actual. Do ponto de vista de base de dados, a decisão de adiar DB é viável no curto prazo, desde que as restrições acima sejam tratadas como obrigatórias para controlar risco operacional até ao momento de migração.