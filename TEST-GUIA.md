# 🧪 Guia de Teste — UniGrade

## Passo 1: Verificar Backend APENAS

**Terminal 1:**
```bash
./run-backend-only.sh
```

Espera pela mensagem:
```
Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

**No browser, testa:**
- http://localhost:8000/api/v1/health → Deve retornar JSON com status "ok"

---

## Passo 2: Testar API de Registo (curl)

**Terminal 2 (diferente):**

Registar novo utilizador:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name":"Seu Nome",
    "email":"seu@email.com",
    "password":"SenhaForte123"
  }'
```

Resposta esperada (201 Created):
```json
{
  "id": "...",
  "name": "Seu Nome",
  "role": "professor",
  "access_token": "...",
  "requires_password_change": false
}
```

---

## Passo 3: Testar API de Login (curl)

Com a mesma email/password:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email_or_student_number":"seu@email.com",
    "password":"SenhaForte123",
    "role":"professor"
  }'
```

Resposta esperada (200 OK):
```json
{
  "id": "...",
  "name": "Seu Nome",
  "role": "professor",
  "access_token": "...",
  "requires_password_change": false
}
```

---

## Passo 4: Iniciar Frontend

**Terminal 3 (novo):**
```bash
./run-frontend-only.sh
```

Espera pela mensagem:
```
  ➜  Local:   http://localhost:5173/
```

Abre: http://localhost:5173/

---

## Passo 5: Testar na UI

1. **Login:** Use as credenciais do Passo 2
2. **Verificar:** Deve mostrar o seu nome (não "Prof. Demo")
3. **Registar nova conta:** Tente registar outro utilizador via UI

---

## ⚠️ Se falhar em algum passo:

| Passo | Problema | Solução |
|-------|----------|---------|
| 1 | Port 8000 já em uso | `pkill -f uvicorn` |
| 2 | "A palavra-passe deve ter..." | Password precisa: 8+ chars + 1 uppercase |
| 3 | Erro 401 | Verificar email/password exatamente |
| 4 | Port 5173 já em uso | `pkill -f "vite\|node"` |
| 5 | "Failed to fetch" | Verificar que Terminal 1 (backend) está a correr |

---

## ✅ Sucesso quando:

- ✅ `http://localhost:8000/api/v1/health` retorna JSON
- ✅ Registar retorna token (201)
- ✅ Login retorna token (200)
- ✅ Frontend abre sem erros em 5173
- ✅ Login na UI mostra o seu nome real
- ✅ Sem "Prof. Demo" em lugar nenhum
