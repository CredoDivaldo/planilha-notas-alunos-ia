# Tela 03 — Portal do Estudante
**Viewport:** 1280px desktop | **Persona:** Estudante

---

## Wireframe Mid-Fi

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ HEADER [1280px]                                                                 │
│  📊 Portal do Estudante                         👤 Ana Silva  22001  [Sair]   │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  SAUDAÇÃO + CONTEXTO                                                           │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │  👋 Olá, Ana!  ·  ING-T1 · Inglês · Semestre 2026/1 · Turma Manhã    │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
│  ┌─────────────────────────────────────────────────────┐  ┌────────────────┐  │
│  │  MINHAS NOTAS                              [📥 PDF]  │  │ CALENDÁRIO     │  │
│  │  ─────────────────────────────────────────────────   │  │ ─────────────  │  │
│  │                                                      │  │ Junho 2026     │  │
│  │  Disciplina: Inglês Técnico                          │  │ ─────────────  │  │
│  │  Docente: Prof. Divaldo Lopes                        │  │ S T Q Q S S D  │  │
│  │  Semestre: 2026/1  ·  Turma: ING-T1                 │  │  1  2  3  4  5  6  7│  │
│  │                                                      │  │  8  9 10 11 12 13 14│  │
│  │  ┌──────────────────────────────────────────────┐   │  │ 15 16 17 18 19 20 21│  │
│  │  │ Componente       │ Peso │ Nota │ Estado       │   │  │ 22 23 24 25 26 27 28│  │
│  │  │ ─────────────────┼──────┼──────┼─────────── │   │  │ 29 30              │  │
│  │  │ Frequência       │  40% │  15  │ ✅ Lançada  │   │  │                    │  │
│  │  │ Exame Final      │  60% │  14  │ ✅ Lançada  │   │  │ 🔵 17 Jun — Exame  │  │
│  │  │ ─────────────────┼──────┼──────┼─────────── │   │  │ 🟠 24 Jun — Recurso│  │
│  │  │ Nota Final       │      │ 14.4 │ ✅ Publicada│   │  │                    │  │
│  │  └──────────────────────────────────────────────┘   │  └────────────────┘  │
│  │                                                      │                      │
│  │  RESULTADO:  ✅ APROVADO(A)                          │  ┌────────────────┐  │
│  │  ════════════════════════════════════════════════   │  │ PRÓXIMOS EVENTOS│  │
│  │                                                      │  │ ─────────────  │  │
│  │  Outras disciplinas do mesmo semestre:               │  │ 📅 17 Jun       │  │
│  │  ┌────────────────────────────────────────────┐     │  │    Exame Inglês │  │
│  │  │ Matemática      │ 12.0 │ ✅ Aprovado       │     │  │    09:00 – Sala 3│  │
│  │  │ Física           │  —   │ ⏳ Pendente       │     │  │                │  │
│  │  └────────────────────────────────────────────┘     │  │ 📅 24 Jun       │  │
│  │                                                      │  │    Recurso Fís. │  │
│  │  ⚠️  Física: nota ainda não publicada.               │  │    14:00 – TBD  │  │
│  └─────────────────────────────────────────────────────┘  └────────────────┘  │
│                                                                                 │
│  CHATBOT WHATSAPP                                                              │
│  ┌────────────────────────────────────────────────────────────────────────┐   │
│  │  💬 Tem dúvidas sobre as suas notas?                                   │   │
│  │  Envie mensagem para o chatbot via WhatsApp e obtenha resposta         │   │
│  │  imediata sobre os seus resultados publicados.                         │   │
│  │  [  💬 Abrir WhatsApp  ]                                               │   │
│  └────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Variante: Nota Não Publicada

```
┌──────────────────────────────────────────────────┐
│  Disciplina: Física                               │
│                                                   │
│  ⏳ As notas desta disciplina ainda não foram    │
│     publicadas pelo docente.                      │
│                                                   │
│  Receberá uma notificação via WhatsApp            │
│  quando os resultados estiverem disponíveis.      │
└──────────────────────────────────────────────────┘
```

---

## Anotações

| Elemento | Comportamento |
|----------|---------------|
| Nota Final | Exibida apenas se `estado = Publicada` (FR9/NFR8) |
| Componentes | Somente componentes marcados como publicados |
| "Nota pendente" | Texto amigável; sem revelar valor (FR19/FR20) |
| Botão PDF | Gera PDF com notas publicadas do semestre |
| Chatbot Banner | Link para WhatsApp do chatbot (Epic 6) |
| Calendário | Eventos do contexto académico activo |
| Sessão expirada | Redireciona para /login com mensagem |

---

## AI Prompt (v0.dev)

```
Build a student portal page for an academic grade system at 1280px:

Layout:
- Header: logo "📊 Portal do Estudante" + student name + student number + logout button
- Welcome banner: "Olá, [Nome]!" + current context (class, subject, semester, shift)
- 2-column layout: 65% left (grades) + 35% right (calendar + upcoming events)

Left column — Grades card:
- Subject title + professor name + semester + "Download PDF" button
- Grade breakdown table: Componente | Peso% | Nota | Estado (published/pending)
- Final grade row in bold: "Nota Final | 14.4 | ✅ Publicada"
- Large result badge: "✅ APROVADO(A)" in green
- Other subjects table (compact): Subject | Grade | Result
- Warning for unpublished subjects: amber info box "nota ainda não publicada"

Right column:
- Mini month calendar with colored event dots
- "Próximos Eventos" list: date + event name + time + location

Bottom banner:
- WhatsApp chatbot invite: "💬 Tem dúvidas?" text + "Abrir WhatsApp" CTA button

Colors: Primary #0D6EFD, Success #15803D, Warning #B45309, Error #B91C1C
No unpublished data should be shown — only published grades
Font: Inter + Tailwind CSS, React + TypeScript, WCAG AA
```
