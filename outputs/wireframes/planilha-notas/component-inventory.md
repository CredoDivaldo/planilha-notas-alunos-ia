# Inventário de Componentes — Atomic Design
**Gerado por:** Uma (UX-Design Expert) | **Data:** 2026-06-05
**Projecto:** Planilha Notas Alunos

---

## Átomos (Atoms)

| ID | Componente | Variantes | Telas |
|----|-----------|-----------|-------|
| A01 | **Button** | primary, secondary, danger, ghost, loading, disabled | Todas |
| A02 | **Input** | text, email, password, number, search, file | 00, 01, 04, 05, 06 |
| A03 | **Label** | default, required (*), error | 00, 04, 05, 06 |
| A04 | **Badge** | success, warning, error, info, neutral | Todas |
| A05 | **Icon** | check, x, lock, warning, upload, calendar, user, send | Todas |
| A06 | **Spinner** | sm, md, lg | 01, 07 |
| A07 | **Divider** | horizontal, vertical | 01, 03, 04 |
| A08 | **Checkbox** | default, checked, indeterminate, disabled | 07 |
| A09 | **Radio** | default, selected, disabled | 07 |
| A10 | **Select** | default, open, disabled, error | 01, 04, 05, 06, 07 |

---

## Moléculas (Molecules)

| ID | Componente | Átomos Base | Telas |
|----|-----------|-------------|-------|
| M01 | **FormField** | Label + Input + HelperText + Error | 00, 04, 06 |
| M02 | **StatusMessage** | Icon + Text + (Close) | Todas |
| M03 | **StatCard** | Label + BigNumber + Trend | 01, 02, 03 |
| M04 | **TableRow** | Cells + ActionButtons | 01, 02, 04, 05 |
| M05 | **SearchBar** | Input + Icon + Button | 02, 04, 05 |
| M06 | **ProgressStep** | Number + Label + Connector | 01, 07 |
| M07 | **EventDot** | ColorDot + Tooltip | 03, 06 |
| M08 | **CalendarDay** | DayNumber + EventDots | 03, 06 |
| M09 | **RadioGroup** | Label + Radio[] + HelperText | 07 |
| M10 | **FileDropzone** | Icon + Text + Button | 01, 05 |

---

## Organismos (Organisms)

| ID | Componente | Moléculas Base | Telas |
|----|-----------|----------------|-------|
| O01 | **AppHeader** | Logo + NavMenu + UserMenu + LogoutBtn | Todas |
| O02 | **StepCard** | ProgressStep + StatusMessage + ActionArea + ResultsTable | 01 |
| O03 | **QuickStatsSidebar** | StatCard[] + WhatsAppStatus | 01 |
| O04 | **GradeTable** | SearchBar + TableHeader + TableRow[] + Pagination | 02, 05 |
| O05 | **ContextTable** | SearchBar + FilterBar + TableRow[] + DetailPanel | 04 |
| O06 | **MonthCalendar** | CalendarHeader + CalendarGrid + EventDot | 03, 06 |
| O07 | **UpcomingEventsList** | EventCard[] + DateGroupHeader | 03, 06 |
| O08 | **PublicationStepper** | ProgressStep[] + StepContent + NavButtons | 07 |
| O09 | **BroadcastResultSummary** | StatCard[] + FailuresList + ActionButtons | 07 |
| O10 | **GradeComponentTable** | TableHeader + EditableRow[] + TotalRow | 04, 05 |

---

## Templates

| ID | Template | Organismos | Telas |
|----|---------|------------|-------|
| T01 | **LoginPage** | CenteredCard + FormField + TabSwitcher | 00 |
| T02 | **DashboardLayout** | AppHeader + ContextBar + MainContent + Sidebar | 01, 02 |
| T03 | **StudentPortal** | AppHeader + WelcomeBanner + GradeSection + CalendarSection | 03 |
| T04 | **DataManagementPage** | AppHeader + Breadcrumb + Toolbar + DataTable + DetailPanel | 04, 05 |
| T05 | **CalendarPage** | AppHeader + CalendarControls + MonthCalendar + Sidebar | 06 |
| T06 | **WizardPage** | AppHeader + ProgressStepper + StepContent + NavigationButtons | 07 |

---

## Estados a Implementar por Componente

### StepCard (O02) — crítico
- `locked` — cinza, colapsado, lista de pré-condições
- `active` — borda azul, expandido, acção disponível
- `completed` — borda verde, colapsado, resumo visível
- `error` — borda vermelha, mensagem de erro, re-tentar

### GradeTable Row (M04) — crítico
- `default` — valores estáticos
- `editing` — célula activa com input inline + guardar/cancelar
- `saving` — spinner, disabled
- `error` — borda vermelha, erro inline

### StatusMessage (M02)
- `success` — verde, ícone ✅
- `info` — azul, ícone ℹ️
- `warning` — âmbar, ícone ⚠️
- `error` — vermelho, ícone ❌
- `dismissible` — com botão ✕

### PublicationStepper (O08)
- Cada step: `pending` | `active` | `completed`
- Botão "Publicar": `disabled` até checkbox confirmação marcada

---

## Notas de Acessibilidade (WCAG AA)

| Requisito | Componente | Implementação |
|-----------|-----------|---------------|
| Focus visível | Todos os interactivos | `focus-visible: outline 2px solid #0D6EFD` |
| Contraste texto | Badge, StatusMessage | Verificar ≥ 4.5:1 em todos os estados |
| `aria-live` | StatusMessage, stats | `aria-live="polite"` para updates; `"assertive"` para erros |
| Labels | FormField, Input | `<label for=...>` ou `aria-label` obrigatório |
| `aria-disabled` | Botões bloqueados | Não usar apenas `disabled`; manter focusável com aria |
| Navegação teclado | Modal, Dropdown | Focus trap em modais; Escape fecha |
| Role semântico | StepCard | `role="region"` + `aria-labelledby` |
| Tabela | GradeTable | `<th scope="col/row">`, `aria-label` na tabela |
