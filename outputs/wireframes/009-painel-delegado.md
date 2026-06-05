# Wireframe 009: Painel Delegado (FR14, FR15)

**Fidelidade:** Low (ASCII)  
**User:** Delegado (João)  
**Requisitos:** FR14-FR15 (permissões limitadas, aprovação professor)

---

## Layout Principal

```
+─────────────────────────────────────────────────────────────────+
│ [Logo]  Planilha de Notas                    João Silva [Sair]  │
+─────────────────────────────────────────────────────────────────+

⚠️  PAINEL DO DELEGADO - Acesso Limitado

Você é delegado de: Turma A (Algoritmos)

+─────────────────────────────────────────────────────────────────+
│ Sidebar                                    │ Main Content        │
│ ═════════════════════════════════════════  │═════════════════════│
│                                            │                     │
│ Dashboard  [●]                             │ Dashboard           │
│ Estudantes (Turma A)                       │ ════════════════════│
│ Preparação de Uploads                      │                     │
│ Auditoria (Turma A)                        │ 📋 Status de Turma  │
│ Perfil                                     │ ───────────────────│
│                                            │                     │
│                                            │ Estudantes: 30      │
│                                            │ Status: Pronto      │
│                                            │                     │
│                                            │ 🚀 Ações Pendentes  │
│                                            │ ───────────────────│
│                                            │                     │
│                                            │ [ Preparar Upload ] │
│                                            │ [ Ver Auditoria ]   │
│                                            │                     │
│                                            │ ⚠️ Ações Bloqueadas │
│                                            │ ───────────────────│
│                                            │                     │
│                                            │ Publicar notas:     │
│                                            │ ❌ Apenas professor │
│                                            │                     │
│                                            │ Criar contexto:     │
│                                            │ ❌ Apenas professor │
│                                            │                     │
│                                            │ Atribuir novo       │
│                                            │ delegado:           │
│                                            │ ❌ Apenas professor │
│                                            │                     │
+─────────────────────────────────────────────────────────────────+
```

---

## Gestão de Estudantes (Delegado - Limitado)

```
Estudantes - Turma A (30)

[ Upload CSV ]  [ + Adicionar Manual ]  [ Submeter para Aprovação ]

┌────────────────────────────────────────────────────────────────┐
│ Nº │ Nome              │ Contacto      │ Ações                  │
├────────────────────────────────────────────────────────────────┤
│ 1  │ João Silva        │ +258 84 123   │ Editar   [Remover ✗]  │
│ 2  │ Ana Costa         │ +258 84 456   │ Editar   [Remover ✗]  │
│ 3  │ Pedro Neves       │ +258 84 789   │ Editar   [Remover ✗]  │
│    │ (27 mais...)      │               │                        │
└────────────────────────────────────────────────────────────────┘

Status: Editável (aguardando submissão)

[ Submeter para Aprovação Professor ]
```

---

## Upload com Submissão (Não Directo)

```
[ Upload CSV ]

Depois de fazer upload:

┌─────────────────────────────────────────────┐
│  Upload Preparado                           │
├─────────────────────────────────────────────┤
│                                             │
│  28 registos válidos                        │
│  2 contactos inválidos                      │
│                                             │
│  Status: ⏳ AGUARDANDO APROVAÇÃO             │
│                                             │
│  ⚠️ Este upload ainda NÃO foi confirmado.    │
│     O professor precisa revisar antes.      │
│                                             │
│  [ Editar ]  [ Submeter ]  [ Cancelar ]    │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Ações Bloqueadas (Feedback Claro)

```
Quando tenta aceder a ações proibidas:

┌─────────────────────────────────────────────┐
│ Publicar Notas                              │
│ ───────────────────────────────────────────│
│                                             │
│ ❌ Apenas o professor pode publicar         │
│    notas.                                   │
│                                             │
│ Para publicar, contacte:                    │
│ 👨‍🏫 Prof. Carlos Silva                       │
│    carlos.silva@universidade.ac             │
│                                             │
│ Você pode:                                  │
│ ✅ Preparar uploads de notas                │
│ ✅ Ajudar a validar dados                   │
│ ✅ Avisar o professor quando pronto         │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Auditoria (Delegado - Turma Própria Apenas)

```
Auditoria - Turma A

┌────────────────────────────────────────────────────────────────┐
│ Data/Hora        │ Operação      │ Quem              │ Resultado │
├────────────────────────────────────────────────────────────────┤
│ 03 Jun 13:45     │ UPLOAD NOTAS  │ Carlos Silva (Prof)│ ✅ 30    │
│ 03 Jun 13:00     │ ATRIB DELEGAD │ Carlos Silva (Prof)│ ✅ João  │
│ 02 Jun 16:30     │ UPLOAD EST    │ João (Delegado)   │ ⏳ Pend. │
│ (mais histórico) │               │                   │          │
└────────────────────────────────────────────────────────────────┘

⚠️ Ver apenas ações de Turma A
   (Não consegue ver outras turmas)
```

---

## Perfil do Delegado

```
Perfil - João Silva

Número de Estudante: 2024001
Email: joao.silva@universidade.ac
Contacto: +258 84 123 456

Delegação:
────────────────────────────

Turma: Turma A
Disciplina: Algoritmos
Semestre: 2026.1
Válida até: 30 Junho 2026

Permissões:
────────────────────────────

✅ Ver estudantes da turma
✅ Ajudar com upload de dados
✅ Ver auditoria da turma
✅ Contactar professor

❌ Publicar notas
❌ Criar contextos
❌ Atribuir novos delegados
❌ Ver outras turmas

[ Remover Delegação ]
(apenas professor pode fazer isto)
```

---

## Notas de Design

- 🔴 **CRÍTICO:** Sempre mostrar "Delegado" no header (FR14)
- 🔴 **CRÍTICO:** Permissões claras em cada página (FR15)
- ✅ Ações bloqueadas explicam o porquê
- ✅ Contacto do professor visível
- ✅ Submissão em vez de directo (FR15)
- ✅ Auditoria limitada à turma própria
- ✅ Não consegue ver outras turmas
- ✅ Não consegue remover delegação a si próprio

---

**Status:** ✅ Wireframe pronto (9 de 9)

---

# 📊 Resumo de Wireframes Criados

| # | Interface | User | Status |
|---|-----------|------|--------|
| 1 | Login Unificado | Todos | ✅ |
| 2 | Dashboard Professor | Professor | ✅ |
| 3 | Criar Contexto | Professor | ✅ |
| 4 | Gestão Estudantes | Prof + Delegado | ✅ |
| 5 | Upload Notas | Professor | ✅ |
| 6 | Publicação/Broadcast | Professor | ✅ 🔴 CRÍTICO |
| 7 | Portal Estudante | Estudante | ✅ |
| 8 | Auditoria | Prof + Delegado | ✅ |
| 9 | Painel Delegado | Delegado | ✅ |

**Total:** 9/9 wireframes de baixa fidelidade criados  
**Próxima Fase:** Especificação detalhada + Mock-ups
