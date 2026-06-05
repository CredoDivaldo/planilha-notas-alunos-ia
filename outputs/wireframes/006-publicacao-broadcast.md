# Wireframe 006: Publicação/Broadcast (FR9, FR10) 🔴 CRÍTICO

**Fidelidade:** Low (ASCII)  
**User:** Professor  
**Requisitos:** FR9-FR10 (confirmação explícita, broadcast manual)

---

## Fluxo Principal

```
Dashboard → Notas & Publicação

┌────────────────────────────────────────────────────────────────┐
│ Notas - Turma A, Algoritmos                                    │
├────────────────────────────────────────────────────────────────┤
│                                             │                  │
│ Status: 📝 Rascunho (não publicado)        │                  │
│ Notas em rascunho: 30                       │                  │
│ Última publicação: 2026-05-28               │                  │
│                                             │                  │
│ ⚠️ HÁ 30 NOTAS PRONTAS PARA PUBLICAÇÃO      │                  │
│                                             │                  │
│ ┌─────────────────────────────────────┐    │                  │
│ │   [Publicar Notas desta Turma]      │    │                  │
│ └─────────────────────────────────────┘    │                  │
│                                             │                  │
└────────────────────────────────────────────────────────────────┘
```

---

## Confirmação Explícita (🔴 CRÍTICO — FR9)

Clicando [ Publicar Notas ]:

```
+─────────────────────────────────────────────┐
│  ⚠️  CONFIRMAÇÃO DE PUBLICAÇÃO              │
├─────────────────────────────────────────────┤
│                                             │
│  Vai enviar notas para 30 estudantes       │
│  via WhatsApp.                              │
│                                             │
│  Isto é uma acção PERMANENTE.               │
│  Os estudantes receberão notificação.       │
│                                             │
│  ───────────────────────────────────────   │
│                                             │
│  Mensagem:                                  │
│                                             │
│  "Olá {{nome}}, tua nota em                │
│   Algoritmos foi publicada."                │
│                                             │
│  ───────────────────────────────────────   │
│                                             │
│  Ou usar template (futuro)                  │
│  [ Template de Mensagem ▼ ]                 │
│                                             │
│  ───────────────────────────────────────   │
│                                             │
│  [ ] Simulação (Dry-run, sem enviar)       │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  [ Cancelar ]  [ Simular ]          │   │
│  └─────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Depois do Dry-run (Simulação)

```
Resultado da Simulação
═════════════════════════════════════════

✅ 30 mensagens seria enviadas
   - João Silva: "Olá João, tua nota..."
   - Ana Costa: "Olá Ana, tua nota..."
   - (28 mais)

⚠️  Sem erros detectados

Confirma envio de verdade?

┌─────────────────────────────────────┐
│  [Cancelar]  [Confirmar Verdade ✓]  │
└─────────────────────────────────────┘
```

---

## Confirmação Final (BOTÃO VERMELHO)

```
+─────────────────────────────────────────────┐
│  CONFIRMAÇÃO FINAL                          │
├─────────────────────────────────────────────┤
│                                             │
│  ⚠️⚠️⚠️  ÚLTIMA CHANCE  ⚠️⚠️⚠️              │
│                                             │
│  Vai enviar 30 notas via WhatsApp.          │
│  Esta acção NÃO pode ser desfeita.          │
│                                             │
│  Confirmo esta publicação ✓ ?               │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  [Cancelar]  [Confirmar Envio ✓]   │   │
│  │              (botão vermelho)        │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  Timestamp: 2026-06-03 14:30                │
│  Professor: Carlos Silva                    │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Resultado do Envio

```
Publicação Concluída ✅
════════════════════════════════════════

Data: 2026-06-03 14:30:15
Operação: BROADCAST SUCESSO

📤 Enviado:        30 estudantes
✅ Entregues:      30
❌ Falhados:       0
⏳ Pendentes:      0

📊 Taxa de sucesso: 100%

Snapshot criado: #PUB-2026-06-03-001

[ Voltar ao Dashboard ]
[ Ver Auditoria ]
[ Repetir Broadcast ]
```

---

## Fluxo de Novo Broadcast (FR10)

Se professor depois **altera as notas**:

```
⚠️ Detectou alteração nas notas
   Última publicação: 2026-06-03 14:30
   Mudanças desde então: 2

[ Publicar Alterações ]  →  (segue mesmo fluxo de confirmação)
```

---

## Notas de Design

- 🔴 **CRÍTICO:** Confirmação explícita **obrigatória** (FR9)
- 🔴 **CRÍTICO:** Botão vermelho para acção final
- ✅ Dry-run para teste antes de verdade
- ✅ Impossível enviar acidentalmente
- ✅ Timestamp e rastreabilidade clara
- ✅ Novo broadcast possível se houver mudanças (FR10)
- ✅ Não deixa sair do modal sem confirmar/cancelar

---

**Status:** ✅ Wireframe pronto  
**Próxima Interface:** Portal Estudante
