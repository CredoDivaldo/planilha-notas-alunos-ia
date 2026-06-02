# Modelos de Dados e Estratégia de Esquema

## Modelo Relacional Inicial

### `users`

**Propósito:** identidade autenticável comum para professor, estudante e operador técnico.

**Atributos-chave:**
- `id`: UUID ou inteiro autoincremental.
- `username`: identificador de login; para estudantes deve aceitar número de estudante.
- `password_hash`: hash Argon2id.
- `role`: `professor`, `student`, `delegate` ou `admin_local` quando necessário para bootstrap.
- `must_change_password`: booleano.
- `is_active`: booleano.
- `created_at`, `updated_at`, `last_login_at`.

**Relações:** um utilizador estudante liga a `students`; um utilizador professor liga a `professors`; permissões de delegado são modeladas por atribuição, não por poder global.

### `students`

**Propósito:** registo académico do estudante.

**Atributos-chave:**
- `id`
- `student_number`: único e obrigatório.
- `full_name`
- `phone`
- `email`
- `current_class_group_id`
- `course_id`

**Relações:** pertence a curso/turma, tem matrículas, notas internas e snapshots publicados.

### `professors`

**Propósito:** identidade académica do professor.

**Atributos-chave:**
- `id`
- `user_id`
- `full_name`
- `email`
- `phone`

**Relações:** tem várias alocações docentes.

### `courses`, `semesters`, `shifts`, `class_groups`, `subjects`

**Propósito:** domínio académico base para contexto operacional.

**Atributos-chave:**
- `code`, `name`, `status` quando aplicável.
- `semester` deve ter período e estado activo/inactivo.
- `shift` representa manhã, tarde, noite ou valor institucional equivalente.

**Relações:** suportam `teaching_assignments`, `enrollments`, eventos de calendário e publicações.

### `teaching_assignments`

**Propósito:** contexto operacional explícito `professor + turma + disciplina + semestre + turno`.

**Atributos-chave:**
- `professor_id`
- `class_group_id`
- `subject_id`
- `semester_id`
- `shift_id`
- `is_active`

**Regra:** deve existir constraint única para impedir duplicação exacta do mesmo contexto para o mesmo professor.

### `enrollments`

**Propósito:** vínculo entre estudante e contexto académico.

**Atributos-chave:**
- `student_id`
- `class_group_id`
- `semester_id`
- `shift_id`
- `status`

**Relações:** permite consolidar várias disciplinas do estudante no mesmo semestre.

### `assessment_definitions`

**Propósito:** componentes de avaliação configuráveis.

**Atributos-chave:**
- `teaching_assignment_id`
- `code`: por exemplo `P1`, `P2`, `Exame`, `Recurso`.
- `weight`
- `max_score`
- `sort_order`

**Nota:** a fórmula oficial está aberta; por isso o modelo guarda componentes e pesos sem fixar regra institucional definitiva.

### `grade_entries`

**Propósito:** notas internas editáveis.

**Atributos-chave:**
- `student_id`
- `teaching_assignment_id`
- `assessment_definition_id`
- `raw_value`
- `normalized_value`
- `status`: `draft`, `validated`, `voided`.
- `source_upload_id`
- `updated_by_user_id`

**Relações:** nunca é lido directamente pelo portal do estudante.

### `calculation_results`

**Propósito:** resultado académico interno derivado.

**Atributos-chave:**
- `student_id`
- `teaching_assignment_id`
- `formula_version`
- `computed_score`
- `derived_state`
- `computed_at`

**Nota:** `derived_state` deve aceitar valor provisório enquanto a fórmula oficial não estiver fechada.

### `publication_snapshots`

**Propósito:** versão publicada e imutável do que o estudante pode ver.

**Atributos-chave:**
- `id`
- `student_id`
- `teaching_assignment_id`
- `broadcast_job_id`
- `snapshot_version`
- `published_score`
- `published_state`
- `published_payload_json`
- `is_current`
- `published_at`

**Regra:** para cada estudante/contexto só uma snapshot deve estar marcada como `is_current=true`.

### `calendar_events` e `published_calendar_snapshots`

**Propósito:** calendário interno e versão publicada de provas, exames e recursos.

**Atributos-chave:**
- `calendar_events`: contexto, tipo, título, data/hora, local, estado interno.
- `published_calendar_snapshots`: payload publicado por contexto e broadcast.

**Regra:** portal lê snapshots publicados, não eventos internos em rascunho.

### `broadcast_jobs` e `notification_deliveries`

**Propósito:** publicação e rastreio de envio.

**Atributos-chave:**
- `broadcast_jobs`: contexto, tipo, actor, estado, canais, totais, `created_at`, `completed_at`.
- `notification_deliveries`: destinatário, canal, destino, estado, erro, tentativa, resposta externa resumida.

**Relações:** snapshots publicados ficam ligados ao `broadcast_job` que os tornou visíveis.

### `audit_log`

**Propósito:** trilha operacional de uploads, alterações, broadcasts, aprovações e acções sensíveis.

**Atributos-chave:**
- `actor_user_id`
- `action`
- `entity_type`
- `entity_id`
- `before_json`
- `after_json`
- `reason`
- `created_at`

## Estratégia de Migração e Bootstrap

- **Novas tabelas:** todas as tabelas acima devem nascer por migração Alembic v1.
- **Tabelas modificadas:** nenhuma tabela existente, porque não há DB aplicacional actual.
- **Índices iniciais:** `students.student_number`, `users.username`, chaves de contexto em `teaching_assignments`, chaves de leitura em `publication_snapshots(student_id, is_current)` e `notification_deliveries(broadcast_job_id, status)`.
- **Bootstrap:** comando Python dedicado deve criar DB limpo, aplicar migrações e criar conta local inicial de professor/admin conforme ambiente.
- **Migração JSON:** comando separado deve importar `data/students.json`, `data/grades-last-upload.json` e `data/match-last.json` para staging auditável ou entidades de domínio, gerando relatório de contagens, rejeições e conflitos.
- **Rollback:** antes de qualquer importação, criar backup timestamped de `data/`; rollback do DB local pode ser feito por cópia do ficheiro SQLite e reversão Alembic em ambiente de desenvolvimento.
