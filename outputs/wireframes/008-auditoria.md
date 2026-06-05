# Wireframe 008: Auditoria/Histórico (FR16)

**Fidelidade:** Low (ASCII)  
**User:** Professor, Delegado (limitado à turma)  
**Requisitos:** FR16 (rastreabilidade de operações)

---

## Layout Principal

```
+────────────────────────────────────────────────────────────────+
│ Auditoria - Turma A, Algoritmos                                │
+────────────────────────────────────────────────────────────────+

Filtros:  [ Por Data ▼ ]  [ Por Operação ▼ ]  [ Por Autor ▼ ]

┌────────────────────────────────────────────────────────────────┐
│ Data/Hora        │ Operação      │ Quem              │ Resultado │
├────────────────────────────────────────────────────────────────┤
│ 03 Jun 14:30     │ BROADCAST     │ Carlos Silva (Prof)│ ✅ 30    │
│ 03 Jun 13:45     │ UPLOAD NOTAS  │ Carlos Silva (Prof)│ ✅ 30    │
│ 03 Jun 13:00     │ ATRIB DELEGAD │ Carlos Silva (Prof)│ ✅ João  │
│ 02 Jun 16:30     │ UPLOAD EST    │ João (Delegado)   │ ⏳ Pend. │
│ 02 Jun 15:15     │ UPLOAD EST    │ Carlos Silva (Prof)│ ✅ 30    │
│ 01 Jun 14:00     │ CRIAR CONTEXTO│ Carlos Silva (Prof)│ ✅       │
│ (mais histórico) │               │                   │          │
└────────────────────────────────────────────────────────────────┘

[Exportar como PDF]  [Imprimir]
```

---

## Detalhes de Operação

Clicando na linha de BROADCAST:

```
+─────────────────────────────────────────────┐
│  Detalhes: BROADCAST                        │
├─────────────────────────────────────────────┤
│                                             │
│ Data/Hora:  03 Junho 2026 14:30:15         │
│ Operação:   BROADCAST (Publicação)          │
│ Professor:  Carlos Silva                    │
│ Turma:      Turma A                         │
│ Disciplina: Algoritmos                      │
│                                             │
│ Resultado:  ✅ SUCESSO                      │
│ Estudantes: 30 enviados, 30 entregues      │
│ Taxa:       100%                            │
│                                             │
│ Snapshot ID: #PUB-2026-06-03-001            │
│                                             │
│ Mensagem:                                   │
│ "Olá {{nome}}, tua nota foi publicada"     │
│                                             │
│ [Voltar]  [Ver Snapshot Publicado]         │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Filtros

### Por Operação
```
[ Mostrar Todos ▼ ]
- Todos
- UPLOAD ESTUDANTES
- UPLOAD NOTAS
- EDIÇÃO NOTAS
- BROADCAST
- ATRIBUIÇÃO DELEGADO
- CRIAR CONTEXTO
```

### Por Data
```
[ Qualquer Data ▼ ]
- Hoje
- Esta semana
- Este mês
- Data específica: [__/__/____]
```

### Por Autor
```
[ Todos ▼ ]
- Carlos Silva (Professor)
- João Silva (Delegado)
```

---

## Relatório de Auditoria

[ Exportar como PDF ]

Gera documento:

```
RELATÓRIO DE AUDITORIA
Turma A - Algoritmos - Junho 2026
═══════════════════════════════════════

Resumo:
- Total de operações: 35
- Uploads de notas: 3
- Uploads de estudantes: 2
- Broadcasts: 1
- Edições: 8
- Mudanças de delegado: 2

Operações por autor:
- Carlos Silva: 32
- João Silva (delegado): 3

Sucesso/Erro:
- ✅ Bem sucedidas: 34
- ⚠️ Com aviso: 1
- ❌ Falhadas: 0

(Detalhes completos abaixo...)
```

---

## Notas de Design

- ✅ Rastreabilidade completa (quem, o quê, quando) (FR16)
- ✅ Mostra claramente "Professor" vs. "Delegado"
- ✅ Resultado de cada operação visível
- ✅ Filtros para pesquisa rápida
- ✅ Exportação para PDF/impressão
- ✅ Delegado vê apenas ações de sua turma
- ✅ Timestamps exactos para rastreabilidade

---

**Status:** ✅ Wireframe pronto  
**Próxima Interface:** Painel Delegado
