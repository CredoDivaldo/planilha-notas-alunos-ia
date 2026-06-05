# Wireframe 005: Upload & Edição de Notas (FR5, FR6)

**Fidelidade:** Low (ASCII)  
**User:** Professor, Delegado (preparação)  
**Requisitos:** FR5-FR6 (importação + validação + edição manual)

---

## Layout Principal

```
+────────────────────────────────────────────────────────────────+
│ Notas - Turma A, Algoritmos                                    │
+────────────────────────────────────────────────────────────────+

Status: 📝 Rascunho (não publicado)

[ Upload CSV ]  [ + Adicionar Manual ]  [ Publicar ]  [ Guardar ]

┌────────────────────────────────────────────────────────────────┐
│ Nº │ Nome              │ Nota   │ Status   │ Acções             │
├────────────────────────────────────────────────────────────────┤
│ 1  │ João Silva        │ 14.5   │ ✅       │ Editar   Remover   │
│ 2  │ Ana Costa         │ 18.0   │ ✅       │ Editar   Remover   │
│ 3  │ Pedro Neves       │ [vazio]│ ⚠️       │ Editar   Remover   │
│ 4  │ Maria Santos      │ ---    │ ❌       │ [sem match]        │
│ 5  │ Carlos Mendes     │ 16.3   │ ✅       │ Editar   Remover   │
│    │ (25 mais...)      │        │          │                    │
└────────────────────────────────────────────────────────────────┘

Resumo:
✅ 28 matched  |  ⚠️ 1 sem nota  |  ❌ 1 sem match | Pronto: [Publicar]
```

---

## Upload CSV (Modal)

```
+─────────────────────────────────────────────┐
│  Upload de Notas (CSV)                      │
├─────────────────────────────────────────────┤
│                                             │
│  Ficheiro: [ Seleccionar ]                  │
│  (esperado: número | nome | nota)           │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Validar e Pré-visualizar           │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Relatório de Validação

```
Resultado da Validação - Notas
═══════════════════════════════════

✅ 28 estudantes matched
   - Notas importadas com sucesso

⚠️  1 sem nota
   - Linha 3: Pedro Neves - [vazio]
   → Adicionar manualmente

❌ 1 sem correspondência
   - Linha 4: Maria Santos - não encontrado em estudantes
   → Verificar número / estudante inexistente?

📊 Intervalo de notas: 0-20 ✓

[ Ver Detalhes ]  [ Corrigir Manualmente ]  [ Confirmar Import ]
```

---

## Edição em Linha

```
Clicando em "Editar" na linha 3:

│ 3  │ Pedro Neves       │ [15.5_____] │ ✅  │ ✓ ✕ │
      Campo editável, permite digitar

Validação em tempo real:
  - Números 0-20 ✓
  - Não permitir valores inválidos ✗
  - Mostrar "Mudou!" quando alterado
```

---

## Edição Manual (Adicionar)

```
[ + Adicionar Manual ]

┌─────────────────────────────────────────────┐
│  Adicionar Nota Manual                      │
├─────────────────────────────────────────────┤
│                                             │
│  Estudante:                                 │
│  ┌──────────────────────────────────────┐   │
│  │ ▼ Maria Santos (#123)                │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Nota:                                      │
│  ┌──────────────────────────────────────┐   │
│  │                                      │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │  Adicionar                           │   │
│  └──────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Estados de Nota

| Status | Significado | Cor | Ícone |
|--------|-----------|-----|-------|
| ✅ | Matched e com nota | Verde | ✓ |
| ⚠️ | Matched mas sem nota | Amarelo | ! |
| ❌ | Sem correspondência | Vermelho | ✗ |
| 📝 | Adicionado manualmente | Azul | + |

---

## Notas de Design

- ✅ Validação **antes** de persistir (FR5)
- ✅ Relatório detalhado (matched vs. unmatched)
- ✅ Edição manual para correções (FR6)
- ✅ Status sempre claro (rascunho vs publicado)
- ✅ Não deixa publicar sem validação OK
- ✅ Delegado pode preparar (mas precisa aprovação professor)

---

**Status:** ✅ Wireframe pronto  
**Próxima Interface:** Publicação/Broadcast
