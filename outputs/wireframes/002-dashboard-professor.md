# Wireframe 002: Dashboard Professor (FR2, FR3)

**Fidelidade:** Low (ASCII)  
**User:** Professor  
**Requisitos:** FR2-FR3 (contextos activos, gestão de disciplinas)

---

## Layout Principal

```
+─────────────────────────────────────────────────────────────────+
│ [Logo]  Planilha de Notas                  Carlos Silva [Logout]│
+─────────────────────────────────────────────────────────────────+

+─────────────────────────────────────────────────────────────────+
│ Sidebar                                    │ Main Content        │
│ ═══════════════════════════════════════════│═════════════════════│
│                                            │                     │
│ Dashboard  [●]                             │ Dashboard           │
│ Contextos académicos                       │ ════════════════════│
│ Estudantes                                 │                     │
│ Notas & Publicação                         │ 📋 Contextos Activos│
│ Auditoria                                  │ ───────────────────│
│ Perfil                                     │                     │
│                                            │ Turma A - Algoritmos│
│                                            │ Semestre 2026.1     │
│                                            │ Turno: Manhã        │
│                                            │ [Mudar Contexto ▼]  │
│                                            │                     │
│                                            │ Ou:                 │
│                                            │ [ + Novo Contexto ] │
│                                            │                     │
│                                            │ ───────────────────│
│                                            │                     │
│                                            │ 📊 Status Rápido    │
│                                            │ ───────────────────│
│                                            │                     │
│                                            │ 30 estudantes       │
│                                            │ 0 notas publicadas  │
│                                            │ 2 broadcasts        │
│                                            │                     │
│                                            │ ───────────────────│
│                                            │                     │
│                                            │ 🚀 Próximas Acções  │
│                                            │ ───────────────────│
│                                            │                     │
│                                            │ [Ir para Estudantes]│
│                                            │ [Ir para Notas]     │
│                                            │ [Ver Auditoria]     │
│                                            │                     │
+─────────────────────────────────────────────────────────────────+
```

---

## Componentes Principais

### Contextos Activos (Dropdown)
```
📋 Contextos Activos
───────────────────

▼ Turma A - Algoritmos (Manhã, Sem 2026.1)

   ┌─────────────────────────────────────────┐
   │ Turma A - Algoritmos (Manhã, S2026.1)  │
   │ Turma B - Estruturas (Tarde, S2026.1)  │
   │ Turma C - Redes (Noite, S2026.2)       │
   └─────────────────────────────────────────┘

[ + Novo Contexto ]
```

### Status Rápido (Cards)
```
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ 30 Estudantes   │  │ 0 Notas Publ.   │  │ 2 Broadcasts     │
│ (inscritos)     │  │ (hoje)          │  │ (este semestre)  │
└─────────────────┘  └─────────────────┘  └──────────────────┘
```

---

## Notas de Design

- ✅ Contexto sempre visível (um clique para mudar)
- ✅ Status rápido (confiança nos números)
- ✅ Atalhos para principais operações
- ✅ Sidebar fixo (desktop-first)
- ✅ Logout fácil (canto superior direito)

---

**Status:** ✅ Wireframe pronto  
**Próxima Interface:** Criar Contexto Académico
