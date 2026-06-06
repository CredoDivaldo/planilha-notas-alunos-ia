# Tela 02 — Vista Técnica do Delegado
**Viewport:** 1280px desktop | **Persona:** Delegado de Turma

---

## Wireframe Mid-Fi

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ HEADER [1280px]                                                                 │
│  📊 Planilha Notas                              👤 Delegado: Carlos M.  [Sair]│
│  ── ── MODO DELEGADO ── Turma: ING-T1  Sem. 2026/1 ── ──                      │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  RESUMO DA TURMA                                                               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌───────────────┐   │
│  │ 👥 Estudantes  │ │ ✅ Notas pub.  │ │ ⏳ Pendentes   │ │ 📵 S/ Contacto│   │
│  │     42         │ │     38         │ │      4         │ │      3        │   │
│  └────────────────┘ └────────────────┘ └────────────────┘ └───────────────┘   │
│                                                                                 │
│ ┌────────────────────────────────────────────────────────────────────────────┐ │
│ │ LISTA DE ESTUDANTES DA TURMA  [somente leitura]                            │ │
│ │                                                                            │ │
│ │  [🔍 Pesquisar por nome ou número]           [Exportar CSV ▾]             │ │
│ │                                                                            │ │
│ │  Nº Estud. │ Nome              │ Disciplina │ Nota  │ Resultado │ Contacto│ │
│ │  ──────────┼───────────────────┼────────────┼───────┼───────────┼─────────│ │
│ │  22001     │ Ana Silva         │ Inglês     │ 14.5  │ ✅ Aprovou│ ✅ OK  │ │
│ │  22002     │ João Costa        │ Inglês     │ 12.0  │ ✅ Aprovou│ ✅ OK  │ │
│ │  22003     │ Maria Neto        │ Inglês     │  8.0  │ ❌ Reprov.│ ✅ OK  │ │
│ │  22004     │ Pedro Lima        │ Inglês     │ 15.0  │ ✅ Aprovou│ ⚠️ S/T│ │
│ │  22005     │ Clara Sousa       │ Inglês     │  —    │ ⏳ Pend.  │ ✅ OK  │ │
│ │  …         │ …                 │ …          │ …     │ …         │ …      │ │
│ │                                                                            │ │
│ │  ← Anterior   Página 1 de 5   Seguinte →                                  │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│ ┌────────────────────────────────────┐ ┌─────────────────────────────────────┐ │
│ │ CONTACTOS COM PROBLEMA             │ │ ESTADO DO SISTEMA                   │ │
│ │ ─────────────────────              │ │ ─────────────────────               │ │
│ │                                    │ │                                     │ │
│ │ ⚠️ Pedro Lima – sem telefone        │ │ WhatsApp: ● Conectado               │ │
│ │ ⚠️ Fátima Cruz – tel. inválido      │ │ Último broadcast: 04/06 às 10:14    │ │
│ │ ⚠️ Rui Gomes   – sem telefone       │ │                                     │ │
│ │                                    │ │ 📋 Notas publicadas: Sim            │ │
│ │ ℹ️ Comunique ao professor para       │ │ 🔒 Edição de notas: bloqueada      │ │
│ │    corrigir estes contactos.        │ │ (acção exclusiva do professor)      │ │
│ └────────────────────────────────────┘ └─────────────────────────────────────┘ │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Anotações

| Elemento | Comportamento |
|----------|---------------|
| Badge "MODO DELEGADO" | Persistente; não removível; cor âmbar (#B45309) |
| Notas na tabela | Visíveis apenas se estado = Publicado (FR8/FR9) |
| Coluna "Contacto" | ✅ = telefone válido; ⚠️ = ausente/inválido |
| Botão exportar CSV | Exporta lista da turma (sem notas não publicadas) |
| Botão editar | Inexistente — delegado é read-only (FR14/FR15) |
| Pesquisa | Filtra em tempo real no lado do cliente |
| "Edição bloqueada" | Tooltip explica que é acção do professor |

---

## Permissões do Delegado (FR14/FR15)

| Acção | Permitido |
|-------|-----------|
| Ver lista de estudantes | ✅ |
| Ver notas publicadas | ✅ |
| Exportar lista CSV | ✅ |
| Editar notas | ❌ |
| Remover estudantes | ❌ |
| Fazer broadcast | ❌ |
| Ver notas não publicadas | ❌ |

---

## AI Prompt (v0.dev)

```
Build a read-only delegate view for an academic class management system at 1280px:

Layout:
- Header: logo + "MODO DELEGADO" amber badge + class info (ING-T1, Sem 2026/1) + user name + logout
- Summary stats row: 4 cards (Estudantes total, Notas publicadas, Pendentes, Sem contacto) — read-only numbers, no actions
- Main data table: student list with columns (Nº, Nome, Disciplina, Nota, Resultado badge, Contacto status)
  - Result badges: green "Aprovou", red "Reprovou", amber "Pendente"
  - Contact status: green check or amber warning
  - NO edit/delete buttons anywhere
  - Search bar + CSV export only
  - Pagination at bottom
- Bottom 2-column grid:
  - Left: "Contactos com problema" — list of students with missing/invalid phone, info message to contact professor
  - Right: System status — WhatsApp connected badge, last broadcast date, "Edição bloqueada" notice

Visual cues that this is read-only: no action buttons in table, amber "MODO DELEGADO" banner, lock icons
Colors: Primary #0D6EFD, Warning #B45309, Success #15803D, Error #B91C1C
Font: Inter + Tailwind CSS, React + TypeScript, WCAG AA
```
