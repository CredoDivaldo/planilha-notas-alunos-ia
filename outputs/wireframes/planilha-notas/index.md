# Wireframes Mid-Fi — Planilha Notas Alunos
**Fidelidade:** Mid-Fi | **Viewport:** Desktop 1280px | **Data:** 2026-06-05
**Agent:** Uma (UX-Design Expert) | **Projeto:** Planilha Notas + WhatsApp

---

## Inventário de Telas

| # | Tela | Persona | Ficheiro |
|---|------|---------|---------|
| 00 | Login (partilhado) | Professor / Estudante / Delegado | [screens/00-login.md](screens/00-login.md) |
| 01 | Painel Operacional do Professor | Docente Operacional | [screens/01-painel-professor.md](screens/01-painel-professor.md) |
| 02 | Vista Técnica do Delegado | Utilizador Técnico / Delegado | [screens/02-vista-delegado.md](screens/02-vista-delegado.md) |
| 03 | Portal do Estudante | Estudante | [screens/03-portal-estudante.md](screens/03-portal-estudante.md) |
| 04 | Gestão de Contextos Académicos | Docente Operacional | [screens/04-contextos-academicos.md](screens/04-contextos-academicos.md) |
| 05 | Gestão de Notas e Componentes | Docente Operacional | [screens/05-gestao-notas.md](screens/05-gestao-notas.md) |
| 06 | Calendário de Provas, Exames e Recursos | Docente / Estudante | [screens/06-calendario.md](screens/06-calendario.md) |
| 07 | Fluxo de Publicação / Broadcast | Docente Operacional | [screens/07-publicacao-broadcast.md](screens/07-publicacao-broadcast.md) |

---

## Artefactos de Suporte

- [flows.md](flows.md) — Diagramas de fluxo de interacção
- [component-inventory.md](component-inventory.md) — Inventário de componentes (Atomic Design)

---

## Design Tokens de Referência

```
Primary:    #0D6EFD   — botões e destaques principais
Secondary:  #475569   — acções secundárias
Success:    #15803D   — estados concluídos
Warning:    #B45309   — pendentes / alertas
Error:      #B91C1C   — erros e falhas
Accent:     #14B8A6   — destaques informativos

Typography: Inter, system-ui, sans-serif
Base unit:  4px (escala: 4/8/16/24/32/48/64)
Breakpoint: 1280px desktop (mobile < 640px)
```

---

## Convenções ASCII Mid-Fi

```
[Button]           — botão (primary)
[Btn ▾]            — botão com dropdown
(• Radio)          — radio button seleccionado
[ ] Checkbox       — checkbox
[Input: text]      — campo de texto
[Select ▾]         — dropdown/select
████ / ░░░░        — progress bar (preenchido / vazio)
🔒 / ✅ / ⚠️ / ❌  — estados: locked / completed / warning / error
─ │ ┌ ┐ └ ┘ ├ ┤   — bordas de containers
·                  — espaço/separador
```
