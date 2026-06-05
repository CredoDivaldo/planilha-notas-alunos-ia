# Wireframe 003: Criar Contexto Académico (FR3, FR4)

**Fidelidade:** Low (ASCII)  
**User:** Professor  
**Requisitos:** FR3-FR4 (contexto = turma + disciplina + semestre + turno)

---

## Wizard/Modal de Criação

```
+─────────────────────────────────────────────┐
│  ✕ Criar Novo Contexto Académico            │
+─────────────────────────────────────────────+

Passo 1 de 4: Semestre
─────────────────────────

Selecionar semestre:

  ○ 2026.1 (Janeiro - Junho)
  ● 2026.2 (Julho - Dezembro)
  ○ 2027.1 (próximo ano)

Ou criar novo semestre:
┌──────────────────────────┐
│ 2027.1                   │
└──────────────────────────┘

[ Voltar ]  [ Seguinte → ]
```

---

## Fluxo Completo

### Passo 1: Semestre
```
Semestre:
  ┌─────────────────────────────────┐
  │ ▼ 2026.1                        │
  └─────────────────────────────────┘
```

### Passo 2: Turno
```
Turno (em que períodos leciona?):
  ☑ Manhã
  ☐ Tarde
  ☐ Noite

(Pode seleccionar múltiplos)
```

### Passo 3: Turma
```
Turma:
  ┌─────────────────────────────────┐
  │ ▼ Turma A                       │
  └─────────────────────────────────┘

Ou criar nova turma:
┌──────────────────────────┐
│ Turma D                  │
└──────────────────────────┘
```

### Passo 4: Disciplina
```
Disciplina:
  ┌─────────────────────────────────┐
  │ ▼ Algoritmos                    │
  └─────────────────────────────────┘

Ou criar nova disciplina:
┌──────────────────────────┐
│ Algoritmos Avançados    │
└──────────────────────────┘
```

---

## Confirmação Final

```
+─────────────────────────────────────────────┐
│  Resumo do Contexto                         │
├─────────────────────────────────────────────┤
│                                             │
│  Semestre:     2026.1                       │
│  Turno:        Manhã                        │
│  Turma:        Turma A                      │
│  Disciplina:   Algoritmos                   │
│                                             │
│  ⚠️  Isto é uma nova combo?                 │
│      Verificar: Turma A + Algoritmos em     │
│      Manhã/2026.1 já existe?                │
│      ✅ Não existe - OK para criar          │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Confirmar Criação                  │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Validações

- ✅ Semestre obrigatório
- ✅ Turma obrigatória
- ✅ Disciplina obrigatória
- ✅ Turno obrigatório
- ✅ Detectar combos duplicadas (não permitir)
- ✅ Mostrar status de validação em tempo real

---

**Status:** ✅ Wireframe pronto  
**Próxima Interface:** Gestão de Estudantes
