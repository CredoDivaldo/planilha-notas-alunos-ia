# Wireframe 007: Portal Estudante (FR12) — Mobile-First

**Fidelidade:** Low (ASCII)  
**User:** Estudante (Ana)  
**Requisitos:** FR12 (consulta notas publicadas, calendário, info académica)  
**Device:** Mobile (primário)

---

## Mobile Layout (Viewport ~360px)

```
┌────────────────────────────┐
│ Logo        Ana Costa [✕]  │
└────────────────────────────┘

Notas Publicadas
════════════════════════════

┌─────────────────────────────┐
│ 📊 Algoritmos               │
│ ─────────────────────────   │
│ Nota: 14.5 / 20            │
│ Publicada: 03 Jun 2026      │
│ [Ver Detalhes]              │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 📊 Estruturas de Dados       │
│ ─────────────────────────   │
│ Nota: 18.0 / 20            │
│ Publicada: 02 Jun 2026      │
│ [Ver Detalhes]              │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 📊 Redes                     │
│ ─────────────────────────   │
│ ⏳ Não publicada            │
│ (à espera de publicação)     │
│ [Notificar-me]              │
└─────────────────────────────┘

(mais disciplinas...)

Informações Académicas
════════════════════════════

👤 Nome: Ana Costa
🎓 Curso: Engenharia Informática
📚 Turma: Turma A
📅 Semestre: 2026.1
📍 Turno: Manhã

Estado Académico
════════════════════════════

📈 Média Geral: 16.8 / 20

Calendário
════════════════════════════

📅 Próximos Eventos:

   🔹 Prova de Redes
      06 Junho, 14:00

   🔹 Exame de Estruturas
      15 Junho, 09:00

   🔹 Recurso Algoritmos
      20 Junho, 10:00

[Ver Calendário Completo]

Notificações
════════════════════════════

🔔 Está activado
   Notificado quando notas forem publicadas

┌─────────────────────────────┐
│  [Menu]   [Perfil]   [Sair] │
└─────────────────────────────┘
```

---

## Desktop Layout (Viewport ~1200px)

```
+────────────────────────────────────────────────────────────────+
│ Logo            Planilha de Notas         Ana Costa [Perfil] [Sair]
+────────────────────────────────────────────────────────────────+

Dashboard Académico
═════════════════════════════════════════════════════════════════

┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ Algoritmos      │  │ Estruturas      │  │ Redes            │
│ ─────────────── │  │ ─────────────── │  │ ────────────────  │
│ 14.5 / 20 ✅    │  │ 18.0 / 20 ✅    │  │ ⏳ Pendente       │
│ Publicada 3Jun  │  │ Publicada 2Jun  │  │ (em breve)        │
└─────────────────┘  └─────────────────┘  └──────────────────┘

(mais cards...)

Informações Académicas         │    Próximos Eventos
═════════════════════════════  │    ═════════════════════════
                               │    
Curso: Eng. Informática       │    🔹 06 Jun - Prova Redes
Turma: Turma A                │    🔹 15 Jun - Exame Estrut.
Semestre: 2026.1              │    🔹 20 Jun - Recurso Alg.
Turno: Manhã                  │    
                               │    [Ver Calendário Completo]
Média Geral: 16.8 / 20        │    

+────────────────────────────────────────────────────────────────+
```

---

## Ver Detalhes da Disciplina

```
+────────────────────────────────┐
│ Algoritmos                      │
├────────────────────────────────┤
│                                │
│ Nota Final: 14.5 / 20 ✅       │
│ Publicada: 03 Junho 2026       │
│                                │
│ Detalhes da Avaliação:         │
│ ──────────────────────         │
│                                │
│ Participação:    10 / 10  ✅   │
│ Trabalho 1:      14 / 15  ⚠️   │
│ Prova 1:         16 / 20  ✅   │
│ Prova 2:         14 / 20  ⚠️   │
│ Projecto Final:  16 / 20  ✅   │
│                                │
│ Total: 70/85 = 14.5/20         │
│                                │
│ [Voltar]                       │
│                                │
└────────────────────────────────┘
```

---

## Notas de Design

- ✅ **Mobile-first** (Ana acessa primariamente do celular)
- ✅ Cards grandes e toque-friendly
- ✅ Carregamento rápido em 4G
- ✅ Apenas notas **publicadas** (não rascunho) (FR12)
- ✅ Data de publicação visível (rastreabilidade)
- ✅ Sem histórico detalhado (NFR8)
- ✅ Calendário integrado
- ✅ Notificações quando notas publicadas
- ✅ Responsivo para desktop também

---

**Status:** ✅ Wireframe pronto  
**Próxima Interface:** Auditoria
