# Epic 7 — Frontend da Plataforma Académica

**Status:** Draft  
**Owner:** @dev  
**Priority:** P0  
**Points Total:** 34  
**Created:** 2026-06-05  
**Created by:** @sm (River)

---

## Overview

Construir o frontend React da plataforma académica completa que substitui o MVP Node.js (`public/index.html`). Consome a API Python/FastAPI do Epic 5. Implementa 8 telas com autenticação, portais por persona e fluxos completos — professor, estudante e delegado.

O frontend é inicializado em `packages/frontend/` como um projecto Vite + React 18 + TypeScript independente, comunicando com o backend via REST sobre `http://localhost:8000`.

---

## Business Context

O Epic 5 entregou uma API Python/FastAPI robusta com autenticação JWT, gestão de contextos académicos, notas, publicação e portal do estudante. O MVP actual (`public/index.html`) não reflecte os fluxos validados nem o design system definido no Epic 4. O Epic 7 fecha este gap, entregando uma interface de utilizador de produção que concretiza os wireframes do UX Design Expert e os requisitos funcionais FR1–FR20.

---

## Scope

### IN — O que este Epic entrega

- Setup completo do projecto frontend (`packages/frontend/`)
- Tela de login unificada para 3 personas (professor, estudante, delegado)
- Painel operacional do professor com 5 StepCards sequenciais
- Gestão de contextos académicos (CRUD completo)
- Gestão de notas com edição inline e upload CSV
- Portal do estudante (mobile-first, só notas publicadas)
- Wizard de publicação / broadcast (4 passos)
- Calendário de provas e exames (professor: edição; estudante: leitura)
- Vista read-only do delegado

### OUT — O que este Epic NÃO entrega

- Backend API (entregue pelo Epic 5)
- Chatbot WhatsApp AI (entregue pelo Epic 6)
- Testes E2E automatizados (escopo futuro)
- PWA / app mobile nativa
- Internacionalização (i18n) além do Português

---

## Stories

| ID | Título | Points | Priority | Owner | Quality Gate | Sprint | Depends On |
|----|--------|--------|----------|-------|--------------|--------|-----------|
| 7.1 | Setup do Projecto Frontend | 3 | P0 | @dev | @qa | 1 | — |
| 7.2 | Login Unificado (Tela 00) | 3 | P0 | @dev | @qa | 1 | 7.1 |
| 7.4 | Contextos Académicos (Tela 04) | 4 | P0 | @dev | @qa | 1 | 7.2 |
| 7.3 | Painel Operacional do Professor (Tela 01) | 5 | P0 | @dev | @qa | 2 | 7.2 |
| 7.5 | Gestão de Notas (Tela 05) | 5 | P0 | @dev | @qa | 2 | 7.4 |
| 7.6 | Portal do Estudante (Tela 03) | 4 | P0 | @dev | @qa | 2 | 7.2 |
| 7.7 | Publicação / Broadcast (Tela 07) | 4 | P1 | @dev | @qa | 3 | 7.5 |
| 7.8 | Calendário (Tela 06) | 3 | P1 | @dev | @qa | 3 | 7.2 |
| 7.9 | Vista Delegado (Tela 02) | 3 | P1 | @dev | @qa | 3 | 7.2 |
| **TOTAL** | | **34** | | | | | |

---

## Dependencies

### Prerequisites (bloqueantes)

- **Epic 5 — Academic Platform Foundation** deve estar **completo** antes de iniciar Sprint 2.
  - Story 5.2: Autenticação JWT e roles → necessário para Story 7.2
  - Story 5.3: Grade Publication Workflow → necessário para Story 7.7
  - Story 5.4: Academic Context Setup → necessário para Story 7.4
  - Story 5.5: Student Portal Read Model → necessário para Story 7.6
  - Story 5.6: Student Portal Calendar → necessário para Story 7.8

- **Story 7.1** é prerequisito de **todas as stories 7.2–7.9**
- **Story 7.2** é prerequisito de **7.3, 7.4, 7.6, 7.8, 7.9**
- **Story 7.4** é prerequisito de **7.5**
- **Story 7.5** é prerequisito de **7.7**

### Design Artefacts (referência)

- Wireframes: `outputs/wireframes/planilha-notas/screens/`
- Component Inventory: `outputs/wireframes/planilha-notas/component-inventory.md`
- Flows: `outputs/wireframes/planilha-notas/flows.md`

---

## Critical Path

```
7.1 → 7.2 ─┬→ 7.3 (painel)
            ├→ 7.4 (contextos) → 7.5 (notas) → 7.7 (broadcast)
            ├→ 7.6 (portal estudante)
            ├→ 7.8 (calendário)
            └→ 7.9 (delegado)
```

---

## Sprint Timeline

### Sprint 1 (Setup + Auth + Base)
| Story | Pontos |
|-------|--------|
| 7.1 Setup do Projecto Frontend | 3 |
| 7.2 Login Unificado | 3 |
| 7.4 Contextos Académicos | 4 |
| **Total** | **10** |

### Sprint 2 (Core Features)
| Story | Pontos |
|-------|--------|
| 7.3 Painel Operacional do Professor | 5 |
| 7.5 Gestão de Notas | 5 |
| 7.6 Portal do Estudante | 4 |
| **Total** | **14** |

### Sprint 3 (Completion)
| Story | Pontos |
|-------|--------|
| 7.7 Publicação / Broadcast | 4 |
| 7.8 Calendário | 3 |
| 7.9 Vista Delegado | 3 |
| **Total** | **10** |

---

## Tech Stack

| Camada | Tecnologia |
|--------|-----------|
| Framework | React 18 + TypeScript |
| Bundler | Vite |
| Styling | Tailwind CSS v3 |
| Components | shadcn/ui |
| Routing | React Router v6 |
| State | React Context + useState |
| HTTP | fetch nativo (ou axios) |
| Backend API | Python/FastAPI em `packages/backend/` |
| Frontend Dir | `packages/frontend/` |
| Package Manager | npm |

### Design Tokens

| Token | Valor |
|-------|-------|
| Primary | `#0D6EFD` |
| Secondary | `#475569` |
| Success | `#15803D` |
| Warning | `#B45309` |
| Error | `#B91C1C` |
| Accent | `#14B8A6` |
| Typography | Inter, system-ui, sans-serif |
| Base Unit | 4px |
| Breakpoint Desktop | 1280px |
| Breakpoint Mobile | 640px |

### API Base

- Base URL: `http://localhost:8000`
- Auth: Bearer token (JWT) via `POST /auth/login`
- Roles: professor, estudante, delegado

---

## Quality Gates

- Cada story requer revisão @qa antes de ser marcada Done
- `npm run lint` sem erros obrigatório em cada story
- `npm run build` sem erros obrigatório em cada story
- WCAG AA obrigatório para componentes de formulário e tabelas
- Testes unitários para componentes críticos (StepCard, GradeTable, AuthContext)

---

## Change Log

| Data | Autor | Descrição |
|------|-------|-----------|
| 2026-06-05 | @sm (River) | Epic criado a partir do handoff ux-to-sm |
