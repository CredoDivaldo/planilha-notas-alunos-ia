# Sprint de Correções UX/UI — UniGrade

**Criado:** 2026-06-11  
**Sessão seguinte:** implementar por waves, por ordem de prioridade

---

## Diagnóstico rápido — causa raiz de múltiplos problemas

> **"failed to fetch" em register, CSV, login" → backend FastAPI NÃO está a correr.**
>
> `npm run dev` na pasta `client/` inicia apenas o Vite (frontend).  
> O FastAPI precisa de ser iniciado SEPARADAMENTE:
> ```bash
> # Terminal 1 — Backend
> cd "Planilha notas alunos IA"
> source .venv/bin/activate   # ou  python -m venv .venv && pip install -e ".[dev]"
> uvicorn backend.app.main:app --reload --port 8000
>
> # Terminal 2 — Frontend
> cd client
> npm run dev
> ```
> O Vite proxy (`vite.config.ts`) encaminha `/auth`, `/api`, etc. → `localhost:8000`.  
> Sem o backend, TODOS os pedidos de rede falham com "failed to fetch".

---

## Wave 1 — Infraestrutura & Auth (BLOQUEADORES) 🔴

**Estimativa: 45 min**

### 1.1 — Script de arranque unificado
- Criar `start-dev.sh` na raiz que lança backend + frontend em paralelo
- Documentar claramente "precisa de 2 terminais" no README

### 1.2 — Validar que o login realmente autentica
- Com o backend a correr, testar `POST /auth/login` com credenciais reais
- Se ainda aceitar qualquer password → investigar `verify_password` em `backend/app/auth/password.py`
- Verificar que a sessão devolvida por `access_token` é guardada no `localStorage`

### 1.3 — Ficheiro CSV de teste
**Formato esperado pelo endpoint `/api/v1/students/upload`:**
```csv
numero_estudante,nome,turma,whatsapp
2023001,Ana Silva,ING-T1,+244923456789
2023002,João Costa,ING-T1,+244912345678
2023003,Maria Santos,ING-T1,
2023004,Pedro Nunes,ING-T1,+244934567890
2023005,Lucia Ferreira,ING-T1,
```
- Criar `docs/test-data/alunos-teste.csv` com 10 linhas reais
- Verificar que o endpoint retorna `{count, students}` 200 OK

---

## Wave 2 — Bugs funcionais (Core) 🟠

**Estimativa: 1h**

### 2.1 — Modal "Editar Contexto" não pré-preenche dados
**Root cause:** `ContextModal` usa `useState(() => ...)` (lazy initializer). O componente está
montado mesmo quando `isOpen=false` (retorna `null` mas não desmonta). Ao reabrir com
novos dados, o state já foi inicializado e não atualiza.

**Fix:** Em `ContextsPage.tsx`, substituir `<ContextModal isOpen={modalOpen} ...>` por:
```tsx
{modalOpen && (
  <ContextModal
    key={`${modalMode}-${editTarget?.id ?? 'new'}`}
    mode={modalMode}
    initialData={editTarget}
    onClose={() => setModalOpen(false)}
    onSubmit={handleModalSubmit}
  />
)}
```
Remover a prop `isOpen` do `ContextModal` (o pai já controla a montagem).

### 2.2 — Selector de contexto em Notas redireciona para o painel
**Root cause:** A `GradesPage` usa o componente `ContextBar` que chama `navigate` ao
mudar de contexto, em vez de atualizar o state local.

**Fix:** `GradesPage` deve gerir o contexto activo internamente com `useState`.
O `ContextBar` deve receber `onContextChange: (ctx: ContextItem) => void` como prop
e chamar essa função em vez de navegar.

### 2.3 — Selector de contexto activo persistente (workspace-style)
**Novo design:** Mover o selector de contexto para um dropdown no topo esquerdo do
`AppLayout` (header principal), visível em todas as páginas protegidas.

- Usar o componente shadcn `<Select>` no header
- O contexto seleccionado fica em estado global (Context API ou localStorage)
- Todas as páginas (Notas, Publicar, Calendário) consomem o contexto activo global
- Remove a `ContextBar` redundante por baixo do header em cada página

**Ficheiros afectados:** `AppLayout`, `AuthContext` (ou novo `ActiveContextContext`),
`GradesPage`, `PublishPage`, `ContextsPage`

---

## Wave 3 — Dark mode completo 🟡

**Estimativa: 45 min**

### 3.1 — PublishPage (`client/src/pages/professor/PublishPage.tsx`)
Substituições massivas:
| Hardcoded | Semântico |
|-----------|-----------|
| `bg-white` | `bg-card` |
| `text-slate-800` | `text-foreground` |
| `bg-slate-100` | `bg-muted` |
| `bg-slate-200` | `bg-muted` |
| `border-slate-*` | `border-border` |
| `bg-white` (textarea) | `bg-input` |
| `focus:ring-[#0D6EFD]/30` | `focus:ring-ring/30` |

### 3.2 — ContextBar (`client/src/components/molecules/ContextBar.tsx`)
| Hardcoded | Semântico |
|-----------|-----------|
| `bg-slate-50` | `bg-muted/50` |
| `border-slate-200` | `border-border` |
| `text-slate-600` | `text-muted-foreground` |
| `bg-white` (SelectTrigger) | remover (shadcn usa bg-background por defeito) |

### 3.3 — MonthCalendar, EventDetailPanel, EventDot, EventModal
```
hover:bg-slate-100     → hover:bg-muted
text-slate-800         → text-foreground
text-slate-700         → text-foreground
bg-slate-50            → bg-muted/50
bg-slate-300           → bg-muted
bg-slate-400           → bg-muted-foreground
border-slate-100       → border-border
border-slate-200       → border-border
bg-[#0D6EFD]           → bg-primary
```

### 3.4 — Backgrounds inconsistentes (Notas e Calendário)
As páginas de Notas e Calendário provavelmente têm `bg-gray-50` ou `bg-white` explícitos.
Uniformizar todos os wrappers de página para `bg-background`.

---

## Wave 4 — WhatsApp/Evolution na interface 🟢

**Estimativa: 45 min**

### 4.1 — Painel do Professor: secção de status WhatsApp
No `DashboardPage` do professor, adicionar uma card "Estado WhatsApp":
- `GET /api/v1/whatsapp/status` → mostra QR code ou "Conectado ✓"
- Botão "Reconectar" → `POST /api/v1/whatsapp/reconnect`
- Botão "Desligar" → `POST /api/v1/whatsapp/disconnect`

### 4.2 — Verificar endpoints no backend
```bash
GET  /api/v1/whatsapp/status      # retorna {connected: bool, qr: str | null}
POST /api/v1/whatsapp/reconnect   # force reconnect
```
Se os endpoints não existirem em `backend/app/routers/` → criar stub básico.

---

## Wave 5 — Polimento final 🔵

**Estimativa: 30 min**

### 5.1 — Título da página html
`<title>UniGrade</title>` — já corrigido em `index.html`.

### 5.2 — Emojis restantes
- `UpcomingEventsList.tsx` ainda tem emojis nos labels de tipo (🔵 Exame, etc.)
- `EventModal.tsx` usa `bg-[#0D6EFD]` (hardcoded blue)
- Substituir por ícones Lucide + cores semânticas

### 5.3 — ContextModal table headers (text-slate-600 → text-muted-foreground)

---

## Ordem de execução recomendada para amanhã

```
Wave 1 → Wave 2.1 + 2.2 → Wave 3 → Wave 2.3 → Wave 4 → Wave 5
```

Wave 1 é o desbloqueador de tudo. Wave 2.1 e 2.2 são bugs simples e rápidos.
Wave 3 é mecânica mas importante visualmente. Wave 2.3 (context global) é a maior refactor.
Wave 4 e 5 são polish.

---

## Ficheiro CSV de teste — conteúdo pronto a usar

Guardar como `docs/test-data/alunos-teste.csv`:
```csv
numero_estudante,nome,turma,whatsapp
2023001,Ana Carolina Silva,ING-T1,+244923456789
2023002,João Miguel Costa,ING-T1,+244912345678
2023003,Maria Beatriz Santos,ING-T1,
2023004,Pedro Henrique Nunes,ING-T1,+244934567890
2023005,Lucia Ferreira Gomes,ING-T1,
2023006,Carlos Eduardo Lima,ING-T1,+244945678901
2023007,Sofia Alexandra Pinto,ING-T1,+244956789012
2023008,Rafael Augusto Moreira,ING-T1,
2023009,Beatriz Helena Carvalho,ING-T1,+244967890123
2023010,André Filipe Rodrigues,ING-T1,
```
