# Wireframe 004: Gestão de Estudantes (FR4, FR14)

**Fidelidade:** Low (ASCII)  
**User:** Professor, Delegado (limitado)  
**Requisitos:** FR4, FR14 (cadastro + delegado)

---

## Layout Principal

```
+────────────────────────────────────────────────────────────────+
│ Estudantes - Turma A (30)                                      │
+────────────────────────────────────────────────────────────────+

[ Upload CSV ]  [ + Adicionar Manual ]  [ Guardar ]

┌────────────────────────────────────────────────────────────────┐
│ Nº │ Nome              │ Contacto      │ Delegado │ Acções      │
├────────────────────────────────────────────────────────────────┤
│ 1  │ João Silva        │ +258 84 123   │ [ ]      │ Editar ✕    │
│ 2  │ Ana Costa         │ +258 84 456   │ [✓]      │ Editar ✕    │
│ 3  │ Pedro Neves       │ +258 84 789   │ [ ]      │ Editar ✕    │
│ 4  │ Maria Santos      │ [inválido]    │ [ ]      │ Editar ✕    │
│ 5  │ Carlos Mendes     │ +258 84 321   │ [ ]      │ Editar ✕    │
│    │ (5 mais...)       │               │          │             │
└────────────────────────────────────────────────────────────────┘

Status: 28 válidos | 1 contacto inválido | 1 duplicado

[ Guardar Alterações ]
```

---

## Upload CSV (Modal)

```
+─────────────────────────────────────────────┐
│  Upload de Estudantes (CSV)                 │
├─────────────────────────────────────────────┤
│                                             │
│  Ficheiro: [ Seleccionar ]                  │
│  (esperado: número | nome | contacto)      │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │    Validar e Pré-visualizar         │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Relatório de Validação

```
Resultado da Validação
═════════════════════════

✅ 28 registos válidos
   - 25 novos
   - 3 actualizações

⚠️  1 contacto inválido
   - Linha 4: Maria Santos - "+258 inválido"
   → Corrigir em "Acções"

⚠️  1 duplicado
   - Linha 2 e 5: João Silva
   → Confirmar qual é o correcto

[ Ver Detalhes ]  [ Cancelar ]  [ Confirmar Import ]
```

---

## Edição em Linha

```
Clicando em "Editar" na linha 4:

│ 4  │ [Maria Santos   ] │ [+258 84 999] │ [ ]  │ ✓ ✕ │
    Permite editar directo na tabela

Clicando em "✕":
Elimina a linha (com confirmação)
```

---

## Atribuição de Delegado

```
Checkbox na coluna "Delegado":

Seleccionar checkbox → Auto-marca como delegado

Se mudar:
  ⚠️  "Tem certeza? Mude para outro delegado se necessário"

O delegado recebe notificação (futuro)
```

---

## Notas de Design

- ✅ Upload com validação **antes** de persistir (FR4)
- ✅ Relatório detalhado de erros
- ✅ Edição em linha para correções rápidas
- ✅ Checkbox delegado fácil (FR14)
- ✅ Confirmação antes de guardar
- ✅ Delegado vê "⚠️ Precisa confirmação professor" quando tenta upload

---

**Status:** ✅ Wireframe pronto  
**Próxima Interface:** Upload & Edição de Notas
