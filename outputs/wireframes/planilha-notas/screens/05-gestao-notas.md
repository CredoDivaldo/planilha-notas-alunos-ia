# Tela 05 — Gestão de Notas e Componentes de Avaliação
**Viewport:** 1280px desktop | **Persona:** Docente Operacional

---

## Wireframe Mid-Fi

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ HEADER [1280px]                                                                 │
│  📊 Planilha Notas    [Painel] [Contextos] [Notas ●] [Calendário] [Publicar]  │
│                                               👤 Prof. Divaldo  [Sair]         │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  BREADCRUMB: Notas > ING-T1 · Inglês Técnico · 2026/1 · Manhã                │
│  [◀ Mudar contexto]                                                            │
│                                                                                 │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │ TOOLBAR                                                                 │   │
│  │  [📥 Importar CSV]  [💾 Guardar alterações]  [🧮 Recalcular]         │   │
│  │  [📤 Publicar notas ▸]  ·  ⚠️  4 notas por preencher                  │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│ ┌────────────────────────────────────────────────────────────────────────────┐ │
│ │  TABELA DE NOTAS — ING-T1 (42 estudantes)                                  │ │
│ │                                                                             │ │
│ │  [🔍 Pesquisar]   [Mostrar: Todos ▾]   [Ordenar: Número ▾]               │ │
│ │                                                                             │ │
│ │  Nº     │ Nome            │ Frequência │ Exame Final │ Nota Final│ Estado  │ │
│ │         │                 │   (40%)    │   (60%)     │           │         │ │
│ │  ───────┼─────────────────┼────────────┼─────────────┼───────────┼─────────│ │
│ │  22001  │ Ana Silva       │  15.0      │  14.0       │  14.4 ✅  │ Lançada│ │
│ │  22002  │ João Costa      │  12.0      │  12.0       │  12.0 ✅  │ Lançada│ │
│ │  22003  │ Maria Neto      │  [Input]   │   8.0       │   ?   —   │ Incompleta│
│ │  22004  │ Pedro Lima      │  14.0      │  [Input]    │   ?   —   │ Incompleta│
│ │  22005  │ Clara Sousa     │  10.0      │  11.0       │  10.6 ✅  │ Lançada│ │
│ │  22006  │ Rui Gomes       │  —         │   —         │   —   —   │ ⚠️ Vazio│ │
│ │  …      │ …               │  …         │  …          │  …        │ …       │ │
│ │                                                                             │ │
│ │  ← Anterior   Página 1 de 5   Seguinte →    [Seleccionar todos]           │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌──────────────────────────────────┐  ┌──────────────────────────────────┐   │
│  │ ESTATÍSTICAS DA TURMA            │  │ HISTÓRICO DE IMPORTAÇÕES         │   │
│  │ ─────────────────────            │  │ ─────────────────────────────    │   │
│  │ Nota média:   12.8               │  │ 04/06 14:32 — CSV importado      │   │
│  │ Nota mais alta: 17.5             │  │  → 38 notas carregadas           │   │
│  │ Nota mais baixa: 5.0             │  │ 01/06 09:10 — CSV importado      │   │
│  │ Aprovados:    31 (73.8%)         │  │  → 42 estudantes carregados      │   │
│  │ Reprovados:    7 (16.7%)         │  │ [Ver log completo ▾]             │   │
│  │ Incompletos:   4  (9.5%)         │  └──────────────────────────────────┘   │
│  └──────────────────────────────────┘                                         │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Variante: Célula em Edição Inline

```
│  22003  │ Maria Neto      │ ┌────────┐ │   8.0       │   ?       │ Incompleta│
│         │                 │ │  9.5   │ │             │           │           │
│         │                 │ └────────┘ │             │           │           │
│         │  [✅ Guardar]  [✕ Cancelar]                                         │
```

---

## Variante: Modal de Importação CSV

```
┌────────────────────────────────────────────────────────┐
│  📥 Importar Notas — ING-T1 · Inglês · 2026/1    [✕]  │
│  ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ──  │
│                                                         │
│  Componente alvo:  [Select ▾ Frequência (40%)]         │
│                                                         │
│  Ficheiro CSV:                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  📁 Arraste o CSV aqui ou  [Escolher ficheiro] │    │
│  └────────────────────────────────────────────────┘    │
│                                                         │
│  Pré-visualização (3 primeiras linhas):                 │
│  ┌──────────────┬────────┐                             │
│  │ numero       │ nota   │                             │
│  │ 22001        │ 15.0   │                             │
│  │ 22002        │ 12.0   │                             │
│  └──────────────┴────────┘                             │
│                                                         │
│  ✅ 38 registos válidos  ⚠️  4 sem correspondência     │
│                                                         │
│  [Cancelar]             [Importar 38 notas]            │
└────────────────────────────────────────────────────────┘
```

---

## Anotações

| Elemento | Comportamento |
|----------|---------------|
| Células editáveis | Duplo-clique activa input inline; Enter ou ✅ confirma |
| Nota Final | Calculada automaticamente após preencher componentes |
| "Guardar alterações" | Activo quando há células modificadas não guardadas |
| "Recalcular" | Força recálculo de Nota Final com fórmula actual (FR7) |
| Estado "Incompleta" | Nota Final não pode ser calculada sem todos os componentes |
| Publicar | Desactivado se há incompletos; abre fluxo Tela 07 |
| Filtros | "Mostrar: Todos / Completos / Incompletos / Vazios" |

---

## AI Prompt (v0.dev)

```
Build a grade management table page for a professor at 1280px:

Layout:
- Header: nav with "Notas" tab active
- Breadcrumb: "Notas > ING-T1 · Inglês Técnico · 2026/1 · Manhã" + "Mudar contexto" link
- Toolbar row: Import CSV button + Save Changes button (disabled when no changes) + Recalculate button + "Publicar notas" primary button + warning count badge

Main data table:
- Columns: Nº, Nome, [dynamic component columns with weight in header], Nota Final, Estado
- Inline editing: double-click cell opens number input with save/cancel icons
- Estado badges: "Lançada" (green), "Incompleta" (amber), "Vazio" (red/warning), "Publicada" (blue)
- Nota Final auto-calculated, shown with check icon when complete
- Search + filter dropdown + sort dropdown above table
- Pagination below

Stats sidebar (or bottom 2-col):
- Left: class statistics (average, high, low, pass rate, incomplete count)
- Right: import history log with timestamps

Import CSV modal:
- Component selector dropdown
- Drag-and-drop file zone
- Preview table (first 3 rows)
- Validation summary: valid count + unmatched count
- Cancel + Import button (shows count)

Colors: Primary #0D6EFD, Success #15803D, Warning #B45309, Error #B91C1C
Font: Inter + Tailwind CSS, React + TypeScript, WCAG AA
```
