# Estratégia de API e Integração

## Princípios

- Endpoints novos usam `/api/v1` e JSON.
- Contratos devem ser documentados em OpenAPI gerado por FastAPI e, quando estabilizados, exportados para `docs/api/openapi.json` ou equivalente.
- Endpoints mutáveis exigem autenticação e autorização por papel.
- Portal do estudante não expõe dados internos, histórico detalhado ou payloads de auditoria.
- API legada Node mantém comportamento até substituição validada por testes.

## Endpoints Iniciais

### Autenticação

- **Método:** `POST`
- **Endpoint:** `/api/v1/auth/login`
- **Propósito:** iniciar sessão por credenciais.
- **Request:**

```json
{
  "username": "1001",
  "password": "temporary-or-user-password"
}
```

- **Response:**

```json
{
  "user": {
    "id": "user-id",
    "role": "student",
    "must_change_password": true
  }
}
```

### Troca de palavra-passe inicial

- **Método:** `POST`
- **Endpoint:** `/api/v1/auth/change-password`
- **Propósito:** cumprir primeiro acesso obrigatório.

```json
{
  "current_password": "temporary-password",
  "new_password": "new-password"
}
```

### Contextos Académicos

- **Método:** `POST`
- **Endpoint:** `/api/v1/academic-contexts`
- **Propósito:** criar contexto `turma + disciplina + semestre + turno` para professor autenticado.

```json
{
  "class_group_id": "class-id",
  "subject_id": "subject-id",
  "semester_id": "semester-id",
  "shift_id": "shift-id"
}
```

### Importação de Notas

- **Método:** `POST`
- **Endpoint:** `/api/v1/imports/grades`
- **Propósito:** importar notas para um contexto académico explícito.
- **Request:** `multipart/form-data` com `context_id` e `file`.
- **Response:**

```json
{
  "import_id": "import-id",
  "accepted_rows": 30,
  "rejected_rows": 2,
  "status": "validated"
}
```

### Publicação

- **Método:** `POST`
- **Endpoint:** `/api/v1/publications/broadcasts`
- **Propósito:** criar broadcast e publicar snapshot actual.

```json
{
  "context_id": "context-id",
  "channels": ["whatsapp"],
  "publication_scope": "grades",
  "dry_run": true
}
```

### Portal do Estudante

- **Método:** `GET`
- **Endpoint:** `/api/v1/portal/me/grades`
- **Propósito:** listar apenas notas publicadas actuais do estudante autenticado.

```json
{
  "student_number": "1001",
  "grades": [
    {
      "subject": "Matemática",
      "semester": "2026-1",
      "published_score": "17",
      "published_state": "published",
      "published_at": "2026-05-28T00:00:00Z"
    }
  ]
}
```

## Chatbot WhatsApp com IA

### Webhook de entrada (Evolution API → sistema)

- **Método:** `POST`
- **Endpoint:** `/api/v1/chatbot/webhook`
- **Propósito:** receber mensagens WhatsApp enviadas por estudantes e desencadear resposta com IA.
- **Autenticação:** token secreto no cabeçalho `X-Webhook-Token` validado contra variável de ambiente `CHATBOT_WEBHOOK_TOKEN`.
- **Request (payload Evolution API):**

```json
{
  "event": "messages.upsert",
  "instance": "nome-da-instancia",
  "data": {
    "key": { "remoteJid": "244912345678@s.whatsapp.net" },
    "message": { "conversation": "Qual é a minha nota de Matemática?" }
  }
}
```

- **Response:** `200 OK` imediato (processamento assíncrono).

### Endpoint de teste (desenvolvimento)

- **Método:** `POST`
- **Endpoint:** `/api/v1/chatbot/test`
- **Propósito:** testar resposta do chatbot sem enviar WhatsApp real (dry-run para desenvolvimento).
- **Autenticação:** papel professor obrigatório.

```json
{
  "student_number": "1001",
  "message": "Qual é a minha nota de Matemática?"
}
```

- **Response:**

```json
{
  "student_number": "1001",
  "ai_response": "Olá! A tua nota de Matemática no semestre 2026-1 é 17 valores, com estado Aprovado.",
  "grades_context_used": ["Matemática / 2026-1 / Turma A"],
  "dry_run": true
}
```

## Integração Evolution API

- **Propósito:** envio WhatsApp principal para broadcasts.
- **Base URL:** `EVOLUTION_BASE_URL`.
- **Autenticação:** cabeçalho `apikey` com `EVOLUTION_API_KEY`.
- **Método de integração:** adapter Python dedicado, isolado do domínio.
- **Endpoints usados no legado:** `/instance/create`, `/instance/connect/{instance}`, `/instance/connectionState/{instance}`, `/message/sendText/{instance}`.
- **Tratamento de erro:** falha por destinatário não deve abortar o lote inteiro; cada entrega fica registada em `notification_deliveries`.
