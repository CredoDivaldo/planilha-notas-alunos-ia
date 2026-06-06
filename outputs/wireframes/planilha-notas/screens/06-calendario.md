# Tela 06 — Calendário de Provas, Exames e Recursos
**Viewport:** 1280px desktop | **Personas:** Docente (edição) / Estudante (leitura)

---

## Wireframe Mid-Fi — Vista Professor (edição)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ HEADER [1280px]                                                                 │
│  📊 Planilha Notas    [Painel] [Contextos] [Notas] [Calendário ●] [Publicar]  │
│                                               👤 Prof. Divaldo  [Sair]         │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  CALENDÁRIO ACADÉMICO                     [+ Adicionar Evento]  [Exportar ▾] │
│                                                                                 │
│  Contexto:  [Select ▾ ING-T1 · Inglês · 2026/1]   [Todos os contextos]      │
│                                                                                 │
│ ┌─────────────────────────────────────────────────────┐ ┌────────────────────┐│
│ │  ◀  Junho 2026  ▶                [Semana] [Mês] [Lista]│ │ LEGENDA           ││
│ │ ─────────────────────────────────────────────────── │ │ ────────────────   ││
│ │ Seg   Ter   Qua   Qui   Sex   Sáb   Dom             │ │ 🔵 Prova           ││
│ │  1     2     3     4     5     6     7               │ │ 🟣 Exame           ││
│ │  8     9    10    11    12    13    14               │ │ 🟠 Recurso         ││
│ │ 15    16   [17]   18    19    20    21               │ │ 🟢 Entrega         ││
│ │              🟣                                      │ │ 🔴 Prova Extra     ││
│ │ 22    23    24    25    26    27    28               │ │ ─────────────────  ││
│ │             🟠                                      │ │                    ││
│ │ 29    30                                            │ │ EVENTO SELECCIONADO││
│ │                                                     │ │                    ││
│ │ [17 Jun — Exame Inglês Técnico]                     │ │ 📅 17 Jun 2026     ││
│ │  09:00 · Sala 3 · ING-T1                            │ │ 🟣 Exame Final     ││
│ │  [✏️ Editar]  [🗑 Eliminar]                          │ │ Inglês Técnico     ││
│ │                                                     │ │ 09:00 – 12:00      ││
│ └─────────────────────────────────────────────────────┘ │ Sala 3 · ING-T1   ││
│                                                          │                    ││
│ ┌─────────────────────────────────────────────────────┐ │ [✏️ Editar evento] ││
│ │ PRÓXIMOS EVENTOS  (7 dias)                          │ │ [🗑 Eliminar]      ││
│ │ ─────────────────────────────────────────────────── │ └────────────────────┘│
│ │ 📅 17 Jun  🟣 Exame Final Inglês — 09:00 Sala 3    │                       │
│ │ 📅 24 Jun  🟠 Recurso Inglês — 14:00 TBD           │                       │
│ │ 📅 28 Jun  🔵 Prova Matemática — 10:00 Sala 5      │                       │
│ └─────────────────────────────────────────────────────┘                       │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Modal: Criar / Editar Evento

```
┌──────────────────────────────────────────────────────────┐
│  📅 Criar Evento Académico                          [✕]  │
│  ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ───   │
│                                                           │
│  Tipo de evento *                                         │
│  (•) 🔵 Prova  (•) 🟣 Exame  (•) 🟠 Recurso            │
│  ( ) 🟢 Entrega  ( ) 🔴 Prova Extra                     │
│                                                           │
│  Descrição *   [Input: ex. Exame Final Inglês Técnico ]  │
│  Contexto *    [Select ▾ ING-T1 · Inglês · 2026/1   ]   │
│  Data *        [Input: 17/06/2026 📅]                    │
│  Hora início   [Input: 09:00]  Hora fim  [Input: 12:00]  │
│  Local         [Input: Sala 3                        ]   │
│  Notas internas[Input: facultativo                   ]   │
│                                                           │
│  Visível para estudantes?  (•) Sim  ( ) Não              │
│                                                           │
│  [Cancelar]                    [Criar Evento]            │
└──────────────────────────────────────────────────────────┘
```

---

## Variante: Vista Estudante (só leitura)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  📅 CALENDÁRIO DE PROVAS E EXAMES        (só leitura — ING-T1 · 2026/1)       │
│                                                                                 │
│  ◀ Junho 2026 ▶                                                               │
│  ─────────────────────────────────────────────────────────────────────────    │
│  [calendário mensal com pontos coloridos — sem botões de edição]              │
│                                                                                 │
│  PRÓXIMOS EVENTOS                                                             │
│  📅 17 Jun — 🟣 Exame Final · Inglês · 09:00 · Sala 3                        │
│  📅 24 Jun — 🟠 Recurso · Inglês · 14:00 · TBD                               │
│  📅 28 Jun — 🔵 Prova · Matemática · 10:00 · Sala 5                          │
│                                                                                 │
│  [Descarregar calendário .ics]                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Anotações

| Elemento | Comportamento |
|----------|---------------|
| Filtro de contexto | "Todos os contextos" agrega eventos de todos |
| Clique no evento | Abre painel lateral com detalhe + editar/eliminar |
| "Visível para estudantes" | Só eventos com este flag aparecem no portal |
| Export | Gera `.ics` (iCal) compatível com Google Calendar / Outlook |
| Vista lista | Alternativa ao calendário para mobile; mais accessível |
| Recurso vs Exame | Tipos distintos; cor e ícone diferente para distinção visual |

---

## AI Prompt (v0.dev)

```
Build an academic calendar page for event management at 1280px:

Layout:
- Header nav with "Calendário" tab active
- Page title + "Adicionar Evento" primary button + "Exportar" dropdown
- Context selector dropdown + "Todos os contextos" checkbox
- 2-column layout: 70% calendar + 30% sidebar

Calendar (left):
- Month navigation arrows + month/year title
- View switcher: Semana | Mês | Lista
- Calendar grid with colored event dots per day:
  - Blue: Prova, Purple: Exame, Orange: Recurso, Green: Entrega, Red: Prova Extra
- Clicking a day or event dot selects it and shows detail in sidebar
- Upcoming events list below calendar (next 7 days, grouped by date)

Sidebar (right):
- Color legend
- Selected event detail panel: date, type badge with color, description, time, location, context
- Edit + Delete action buttons (professor only — hide for students)

Create/Edit modal:
- Event type radio group (with color indicator per type)
- Description text input
- Context dropdown
- Date picker
- Start/end time inputs
- Location text input
- "Visível para estudantes" toggle
- Cancel + Create/Save buttons

Student read-only variant: same layout but no create/edit buttons, add "Download .ics" button

Colors: #3B82F6 (prova), #8B5CF6 (exame), #F97316 (recurso), #22C55E (entrega), #EF4444 (extra)
Font: Inter + Tailwind CSS, React + TypeScript, WCAG AA
```
