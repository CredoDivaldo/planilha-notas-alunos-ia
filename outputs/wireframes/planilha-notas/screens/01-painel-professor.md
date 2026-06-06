# Tela 01 — Painel Operacional do Professor
**Viewport:** 1280px desktop | **Persona:** Docente Operacional

---

## Wireframe Mid-Fi

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ HEADER [1280px]                                                                 │
│  📊 Planilha Notas    [Painel] [Contextos] [Notas] [Calendário] [Publicar]     │
│                                               👤 Prof. Divaldo  [Sair]         │
├────────────────────────────────────────────────────────────────────────────────┤
│ CONTEXT BAR                                                                    │
│  Contexto activo: [Select ▾ ING-T1 · Inglês · 2026/1 · Manhã]  [+ Novo]      │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PROGRESS STEPPER                                                              │
│  ──────────────────────────────────────────────────────────────────────        │
│  ① Upload      ② Upload      ③ Gerar        ④ Conectar     ⑤ Disparar        │
│  Estudantes    Notas         Match           WhatsApp        Mensagens          │
│  ✅ Completo   ✅ Completo   ⚙️  Activo      🔒 Bloqueado   🔒 Bloqueado       │
│  ████████████  ████████████  ████░░░░░░░░    ░░░░░░░░░░░░   ░░░░░░░░░░░░      │
│  ──────────────────────────────────────────────────────────────────────        │
│                                                                                 │
│ ┌─────────────────────────────────────────┐  ┌───────────────────────────┐    │
│ │ STEP CARD — ③ Gerar Match  [ACTIVO]     │  │ ESTATÍSTICAS RÁPIDAS      │    │
│ │                                          │  │ ─────────────────────     │    │
│ │  ✅ 142 estudantes carregados            │  │ 📥 Estudantes   142       │    │
│ │  ✅ 138 notas importadas                 │  │ 📋 Notas        138       │    │
│ │                                          │  │ 🔗 Matched      131       │    │
│ │  [   🔄 Gerar Match   ]                  │  │ ❌ Sem match      7       │    │
│ │                                          │  │ 📵 Tel. inválido  4       │    │
│ │  ─── Último match: 14:32 ───             │  │ ─────────────────────     │    │
│ │                                          │  │ 📤 Enviados       0       │    │
│ │  ┌────────────────────────────────────┐  │  │ ⚠️  Falhas         0       │    │
│ │  │ Nº    Nome          Nota  Status   │  │  └───────────────────────────┘    │
│ │  │ 2201  Ana Silva     14.5  ✅ Match │  │                                   │
│ │  │ 2202  João Costa    12.0  ✅ Match │  │  ┌───────────────────────────┐    │
│ │  │ 2203  Maria Neto    —     ❌ S/N.  │  │  │ WHATSAPP STATUS           │    │
│ │  │ 2204  Pedro Lima    10.0  ⚠️ S/Tel │  │  │ ─────────────────────     │    │
│ │  │ …     …             …     …        │  │  │ ● Conectado               │    │
│ │  │                [Ver todos 131 ▾]   │  │  │ ING-T1-2026               │    │
│ │  └────────────────────────────────────┘  │  │ [🔄 Verificar estado]     │    │
│ └─────────────────────────────────────────┘  └───────────────────────────┘    │
│                                                                                 │
│ ┌─────────────────────────────────────────┐  ┌───────────────────────────┐    │
│ │ STEP CARD — ④ Conectar WhatsApp  🔒     │  │ STEP CARD — ⑤ Disparar 🔒│    │
│ │                                          │  │                           │    │
│ │  Pré-condição:                           │  │  Pré-condição:            │    │
│ │  ❌ Match não gerado                     │  │  ❌ WhatsApp não ligado   │    │
│ │                                          │  │  ❌ Match pendente        │    │
│ │  [Expandir para conectar]                │  │                           │    │
│ └─────────────────────────────────────────┘  └───────────────────────────┘    │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Variante: Step 4 — Conectar WhatsApp (expandido)

```
┌─────────────────────────────────────────────────────┐
│ STEP CARD — ④ Conectar WhatsApp  [ACTIVO]            │
│                                                      │
│  [+ Criar instância]  [🔄 Estado]  [🗑 Remover]     │
│                                                      │
│  Sub-passo:  ( ) Criar  (•) Conectar  ( ) Verificar │
│                                                      │
│  ┌──────────────┐  QR válido por 45s               │
│  │              │  ⏱ 00:38                          │
│  │  [QR CODE]   │                                   │
│  │  180x180     │  Aponte a câmara do WhatsApp       │
│  │              │  para este código.                 │
│  └──────────────┘                                   │
│                                                      │
│  [🔄 Gerar novo QR]      [Verificar conexão →]      │
└─────────────────────────────────────────────────────┘
```

---

## Variante: Step 5 — Disparar (expandido)

```
┌─────────────────────────────────────────────────────┐
│ STEP CARD — ⑤ Mensagem e Disparo  [ACTIVO]          │
│                                                      │
│  Template da mensagem:                               │
│  ┌────────────────────────────────────────────────┐  │
│  │ Olá {{nome}}, a sua nota de {{disciplina}}     │  │
│  │ é {{nota}}. Resultado: {{resultado}}.          │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  Destinatários: 131 alunos com match válido          │
│                                                      │
│  Modo de envio:                                      │
│  (•) Simulação (Dry Run) — sem envio real            │
│  ( ) Envio Real — confirmar antes de disparar        │
│                                                      │
│  [  🚀 Disparar Simulação  ]   [Envio real ▸]       │
│                                                      │
│  ─── Resultado do último envio ───                   │
│  ✅ 128 enviados   ⚠️ 3 falhas   —                   │
└─────────────────────────────────────────────────────┘
```

---

## Anotações

| Elemento | Comportamento |
|----------|---------------|
| Context Bar | Select persistente; muda contexto em toda a página |
| Progress Stepper | Clicável apenas para etapas ✅ concluídas |
| Step Cards bloqueados | Exibem lista de pré-condições em falta |
| Tabela de match | Paginação leve; "Ver todos" abre modal/drawer |
| Estatísticas rápidas | Actualizam em tempo real após cada operação |
| WhatsApp status | Badge verde/vermelho; polling a cada 30s |
| Botão "Envio real" | Abre modal de confirmação (Story 4.6) |

---

## Estados dos Step Cards

| Estado | Visual | Acção |
|--------|--------|-------|
| `locked` | 🔒 Header cinza, corpo colapsado, pré-condições listadas | Não interactível |
| `active` | Borda #0D6EFD, header azul, corpo expandido | Acções disponíveis |
| `completed` | ✅ Header verde, corpo colapsado, resumo visível | Clique expande |
| `error` | ❌ Borda #B91C1C, mensagem de erro inline | Re-tentar disponível |

---

## AI Prompt (v0.dev)

```
Build a professor's operational dashboard for an academic grade management system at 1280px:

Layout:
- Top header: logo "📊 Planilha Notas", horizontal nav (Painel, Contextos, Notas, Calendário, Publicar), user avatar + name right-aligned
- Context bar below header: dropdown selector "Contexto activo" + "Novo contexto" button
- Progress stepper: 5 numbered steps (Upload Estudantes, Upload Notas, Gerar Match, Conectar WhatsApp, Disparar) with states: completed (green check), active (blue border pulsing), locked (gray lock icon), error (red X)
- Main 2-column layout: 70% left (active step card expanded) + 30% right (quick stats + WhatsApp status)
- Remaining locked step cards below in a 2-column grid, collapsed with pre-conditions list

Step Card (active state):
- Blue left border, title + state badge
- Pre-conditions checklist (green checks / red X)
- Primary action button (full width)
- Results table (compact, max 5 rows + "view all" link)

Quick Stats sidebar:
- Icon + label + number for: Estudantes, Notas, Matched, Sem match, Tel. inválido, Enviados, Falhas
- WhatsApp connection status badge (green dot = connected)

Colors: Primary #0D6EFD, Success #15803D, Error #B91C1C, Warning #B45309
Font: Inter + Tailwind CSS, React + TypeScript, WCAG AA
```
