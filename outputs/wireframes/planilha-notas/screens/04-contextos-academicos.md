# Tela 04 — Gestão de Contextos Académicos
**Viewport:** 1280px desktop | **Persona:** Docente Operacional

---

## Wireframe Mid-Fi

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ HEADER [1280px]                                                                 │
│  📊 Planilha Notas    [Painel] [Contextos ●] [Notas] [Calendário] [Publicar]  │
│                                               👤 Prof. Divaldo  [Sair]         │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  GESTÃO DE CONTEXTOS ACADÉMICOS                 [+ Criar Contexto]            │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                                                                                 │
│  [🔍 Filtrar por turma, disciplina ou semestre]  [Semestre ▾]  [Turno ▾]     │
│                                                                                 │
│ ┌────────────────────────────────────────────────────────────────────────────┐ │
│ │  Turma      │ Disciplina          │ Semestre │ Turno   │ Alunos │ Acções  │ │
│ │  ───────────┼─────────────────────┼──────────┼─────────┼────────┼─────────│ │
│ │  ING-T1     │ Inglês Técnico      │ 2026/1   │ Manhã   │ 42     │ [✏️][🗑]│ │
│ │  ING-T2     │ Inglês Técnico      │ 2026/1   │ Tarde   │ 38     │ [✏️][🗑]│ │
│ │  MAT-T1     │ Matemática          │ 2026/1   │ Manhã   │ 40     │ [✏️][🗑]│ │
│ │  FIS-T1     │ Física              │ 2025/2   │ Manhã   │ 35     │ [✏️][🗑]│ │
│ │  QUI-T1     │ Química             │ 2025/2   │ Tarde   │ 37     │ [✏️][🗑]│ │
│ │  …          │ …                   │ …        │ …       │ …      │ …       │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│ ┌──────────────────────────────────────────────┐                               │
│ │  DETALHE: ING-T1 · Inglês Técnico · 2026/1  │                               │
│ │  ─── ─── ─── ─── ─── ─── ─── ─── ─── ───   │                               │
│ │                                              │                               │
│ │  COMPONENTES DE AVALIAÇÃO                    │                               │
│ │  ┌──────────────────────┬───────┬──────────┐ │                               │
│ │  │ Componente           │ Peso  │ Acções   │ │                               │
│ │  │ ─────────────────────┼───────┼───────── │ │                               │
│ │  │ Frequência           │  40%  │ [✏️]     │ │                               │
│ │  │ Exame Final          │  60%  │ [✏️]     │ │                               │
│ │  │ Total                │ 100%  │          │ │                               │
│ │  └──────────────────────┴───────┴──────────┘ │                               │
│ │  [+ Adicionar componente]                     │                               │
│ │                                              │                               │
│ │  ESTUDANTES ASSOCIADOS  42 alunos            │                               │
│ │  [👥 Ver estudantes]  [+ Importar via CSV]   │                               │
│ │                                              │                               │
│ │  DELEGADO ATRIBUÍDO                          │                               │
│ │  Carlos Mendes (22009)   [Alterar delegado]  │                               │
│ └──────────────────────────────────────────────┘                               │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Modal: Criar / Editar Contexto

```
┌─────────────────────────────────────────────────────────┐
│  ✏️  Criar Contexto Académico                       [✕]  │
│  ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ─── ───  │
│                                                          │
│  Turma *         [Input: ex. ING-T1              ]      │
│  Disciplina *    [Select ▾ Inglês Técnico        ]      │
│  Semestre *      [Select ▾ 2026/1                ]      │
│  Turno *         [Select ▾ Manhã                 ]      │
│  Curso           [Select ▾ Engenharia Informática]      │
│                                                          │
│  Componentes de Avaliação                                │
│  ┌───────────────────────────────────────┐              │
│  │ Componente        │ Peso (%) │ [🗑]   │              │
│  │ Frequência        │ [Input:40]│ [🗑]   │              │
│  │ Exame Final       │ [Input:60]│ [🗑]   │              │
│  │                   │ Total: 100│        │              │
│  └───────────────────────────────────────┘              │
│  [+ Componente]                                          │
│                                                          │
│  ⚠️  Os pesos devem somar 100%.                          │
│                                                          │
│  [Cancelar]                    [Criar Contexto]          │
└─────────────────────────────────────────────────────────┘
```

---

## Anotações

| Elemento | Comportamento |
|----------|---------------|
| Filtros | Combinam-se; resultados actualizam sem reload |
| Botão 🗑 no contexto | Modal de confirmação antes de eliminar |
| Painel de detalhe | Slide-in lateral ao clicar numa linha; ou abaixo da tabela |
| Total pesos | Validação em tempo real; bloqueia guardar se ≠ 100% |
| Delegado | Select de estudantes da turma; permissão técnica limitada |
| "Importar via CSV" | Reutiliza fluxo do Painel (Step 1) |

---

## AI Prompt (v0.dev)

```
Build an academic contexts management page for a professor at 1280px:

Layout:
- Header: nav with "Contextos" tab active (blue underline indicator)
- Page title "Gestão de Contextos Académicos" + "Criar Contexto" button (primary, top-right)
- Filter bar: text search + "Semestre" dropdown + "Turno" dropdown

Main content:
- Data table: Turma | Disciplina | Semestre | Turno | Alunos count | Edit + Delete action buttons
- Below table: detail panel (slides in or shows below) when row is selected:
  - Assessment components sub-table: Componente | Peso% | Edit button — with total row
  - "Adicionar componente" link button
  - Students section: count + "Ver estudantes" + "Importar CSV" buttons
  - Delegate assignment: student name + "Alterar" link

Modal (create/edit context):
- Form fields: Turma (text), Disciplina (select), Semestre (select), Turno (select), Curso (select)
- Dynamic assessment components table with weight inputs — real-time total validation (must equal 100%)
- Warning if total ≠ 100%
- Cancel + Submit buttons

Colors: Primary #0D6EFD, Warning #B45309
Font: Inter + Tailwind CSS, React + TypeScript, WCAG AA
```
