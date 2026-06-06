# Tela 07 — Fluxo de Publicação / Broadcast
**Viewport:** 1280px desktop | **Persona:** Docente Operacional

---

## Wireframe Mid-Fi — Passo 1: Revisão

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ HEADER [1280px]                                                                 │
│  📊 Planilha Notas    [Painel] [Contextos] [Notas] [Calendário] [Publicar ●]  │
│                                               👤 Prof. Divaldo  [Sair]         │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  PUBLICAÇÃO DE NOTAS                                                           │
│                                                                                 │
│  ① Revisão  ──────  ② Audiência  ──────  ③ Canais  ──────  ④ Confirmar       │
│  ● ──────────────────────── ○ ──────────────────────── ○ ─────────────── ○   │
│                                                                                 │
│ ┌────────────────────────────────────────────────────────────────────────────┐ │
│ │  CONTEXTO: ING-T1 · Inglês Técnico · 2026/1 · Manhã                       │ │
│ │                                                                            │ │
│ │  RESUMO DAS NOTAS A PUBLICAR                                               │ │
│ │  ┌──────────────────────────────────────────────────────────────────────┐  │ │
│ │  │ Nº      │ Nome            │ Freq.│ Exame│ Nota Final│ Resultado      │  │ │
│ │  │ ────────┼─────────────────┼──────┼──────┼───────────┼────────────── │  │ │
│ │  │ 22001   │ Ana Silva       │ 15.0 │ 14.0 │   14.4    │ ✅ Aprovado   │  │ │
│ │  │ 22002   │ João Costa      │ 12.0 │ 12.0 │   12.0    │ ✅ Aprovado   │  │ │
│ │  │ 22003   │ Maria Neto      │  9.5 │  8.0 │    8.7    │ ❌ Reprovado  │  │ │
│ │  │ …       │ …               │ …    │ …    │   …       │ …             │  │ │
│ │  │ 38 alunos com notas completas   ·   4 incompletos (excluídos)        │  │ │
│ │  └──────────────────────────────────────────────────────────────────────┘  │ │
│ │                                                                            │ │
│ │  ⚠️  4 estudantes com notas incompletas NÃO serão incluídos nesta        │ │
│ │      publicação. [Ver lista de excluídos ▾]                               │ │
│ │                                                                            │ │
│ │  Esta acção tornará as notas visíveis no Portal do Estudante.             │ │
│ │  Estudantes serão notificados pelo canal seleccionado.                    │ │
│ │                                                                            │ │
│ │                              [Cancelar]  [Avançar: Audiência →]           │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Passo 2: Audiência

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  ① Revisão  ──── ✅  ② Audiência  ──────  ③ Canais  ──────  ④ Confirmar      │
│                                                                                │
│ ┌────────────────────────────────────────────────────────────────────────────┐ │
│ │  SELECCIONAR AUDIÊNCIA                                                     │ │
│ │                                                                            │ │
│ │  (•) Todos os alunos com nota completa  (38 alunos)                       │ │
│ │  ( ) Apenas aprovados  (31 alunos)                                        │ │
│ │  ( ) Apenas reprovados  (7 alunos)                                        │ │
│ │  ( ) Selecção manual  [Abrir lista de selecção ▾]                        │ │
│ │                                                                            │ │
│ │  Audiência seleccionada:  ● 38 alunos                                     │ │
│ │  ⚠️  3 sem número de telefone válido (excluídos automaticamente)           │ │
│ │                                                                            │ │
│ │                      [← Revisão]  [Avançar: Canais →]                     │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Passo 3: Canais

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  ① Revisão ✅  ② Audiência ✅  ③ Canais  ──────  ④ Confirmar                 │
│                                                                                │
│ ┌────────────────────────────────────────────────────────────────────────────┐ │
│ │  SELECCIONAR CANAIS DE NOTIFICAÇÃO                                         │ │
│ │                                                                            │ │
│ │  [✅] 💬 WhatsApp  (principal)  ● Conectado · 35 com tel. válido           │ │
│ │  [ ] 📧 Email      (opcional)   ○ Não configurado                          │ │
│ │  [ ] Apenas Portal (sem notificação)                                       │ │
│ │                                                                            │ │
│ │  ─── Template da mensagem WhatsApp ───                                    │ │
│ │  ┌────────────────────────────────────────────────────────────────────┐   │ │
│ │  │ Olá {{nome}}, a sua nota de {{disciplina}} (Sem. {{semestre}})    │   │ │
│ │  │ é {{nota_final}}. Resultado: {{resultado}}.                        │   │ │
│ │  │ Consulte os detalhes no portal: {{link_portal}}                   │   │ │
│ │  └────────────────────────────────────────────────────────────────────┘   │ │
│ │                                                                            │ │
│ │  Pré-visualização para Ana Silva:                                          │ │
│ │  ┌────────────────────────────────────────────────────────────────────┐   │ │
│ │  │ Olá Ana, a sua nota de Inglês Técnico (Sem. 2026/1) é 14.4.       │   │ │
│ │  │ Resultado: Aprovado. Consulte os detalhes no portal: …            │   │ │
│ │  └────────────────────────────────────────────────────────────────────┘   │ │
│ │                                                                            │ │
│ │                   [← Audiência]  [Avançar: Confirmar →]                   │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Passo 4: Confirmar e Publicar

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  ① Revisão ✅  ② Audiência ✅  ③ Canais ✅  ④ Confirmar                      │
│                                                                                │
│ ┌────────────────────────────────────────────────────────────────────────────┐ │
│ │  RESUMO DA PUBLICAÇÃO                                                      │ │
│ │                                                                            │ │
│ │  ┌──────────────────────────────────────────────────────────────────────┐  │ │
│ │  │ Contexto:      ING-T1 · Inglês Técnico · 2026/1 · Manhã            │  │ │
│ │  │ Audiência:     38 alunos (todos com nota completa)                  │  │ │
│ │  │ Excluídos:     3 sem telefone válido + 4 notas incompletas          │  │ │
│ │  │ Canal:         💬 WhatsApp — 35 destinatários efectivos             │  │ │
│ │  │ Notas visíveis no portal: Imediatamente após confirmar              │  │ │
│ │  └──────────────────────────────────────────────────────────────────────┘  │ │
│ │                                                                            │ │
│ │  ┌──────────────────────────────────────────────────────────────────────┐  │ │
│ │  │ ⚠️  ATENÇÃO                                                           │  │ │
│ │  │ Esta acção é irreversível sem novo broadcast.                        │  │ │
│ │  │ As notas ficarão visíveis no portal assim que confirmar.             │  │ │
│ │  │ Mensagens WhatsApp serão enviadas a 35 estudantes.                  │  │ │
│ │  └──────────────────────────────────────────────────────────────────────┘  │ │
│ │                                                                            │ │
│ │  [ ] Confirmo que revi as notas e autorizo a publicação.                  │ │
│ │                                                                            │ │
│ │  [← Canais]   [🚀 Publicar e Enviar Notificações]  ← (só activo com ✅)  │ │
│ └────────────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Passo 5: Resultado do Broadcast

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  ✅ PUBLICAÇÃO CONCLUÍDA — ING-T1 · Inglês Técnico · 2026/1                   │
│  04/06/2026 às 15:47                                                          │
│                                                                                │
│  ┌────────────────────────┐ ┌───────────────────────┐ ┌─────────────────────┐ │
│  │ ✅ Publicadas no portal│ │ 💬 WhatsApp enviados   │ │ ❌ Falhas de envio  │ │
│  │         38              │ │         33             │ │          2          │ │
│  └────────────────────────┘ └───────────────────────┘ └─────────────────────┘ │
│                                                                                │
│  Falhas (2):                                                                   │
│  • Maria Cruz (22019) — falha na API (timeout)                                │
│  • Rui Alves (22031) — número bloqueado                                       │
│                                                                                │
│  [🔄 Re-enviar para falhados]  [📥 Exportar relatório]  [← Voltar ao painel] │
└────────────────────────────────────────────────────────────────────────────────┘
```

---

## Anotações

| Elemento | Comportamento |
|----------|---------------|
| Progress stepper | Etapas anteriores marcadas ✅; clicáveis para rever |
| Checkbox de confirmação | Obrigatório para activar botão "Publicar" (FR8/CR5) |
| "Publicar" | Uma única confirmação humana explícita; sem automação silenciosa |
| Excluídos automáticos | Sem telefone válido ou nota incompleta |
| Re-enviar falhados | Apenas reenvia para quem falhou; não republica |
| Estado portal | Muda para `publicado` imediatamente após confirmar |

---

## AI Prompt (v0.dev)

```
Build a multi-step grade publication flow for a professor at 1280px:

4-step wizard with progress stepper at top (step indicator: filled circle = current, check = done, empty = upcoming):

Step 1 — Revisão:
- Context label
- Preview table: student list with all grade components + final grade + result badge
- Warning about incomplete students excluded from publication
- Cancel + Next buttons

Step 2 — Audiência:
- Radio group: All students / Approved only / Rejected only / Manual selection
- Selected count + warning about students without valid phone
- Back + Next buttons

Step 3 — Canais:
- Checkbox list: WhatsApp (connected badge + recipient count) / Email (not configured) / Portal only
- Editable message template with {{variable}} placeholders
- Live preview with first student's data filled in
- Back + Next buttons

Step 4 — Confirmar:
- Summary box: context, audience, excluded, channel, portal visibility
- Warning box (amber): irreversible action notice
- Mandatory confirmation checkbox — publish button disabled until checked
- Back + "🚀 Publicar e Enviar" primary button

Result screen:
- 3 stat cards: Published, Sent, Failed
- Failures list with name + reason
- Action buttons: Re-send to failed / Export report / Back to dashboard

Colors: Primary #0D6EFD, Success #15803D, Warning #B45309, Error #B91C1C
Font: Inter + Tailwind CSS, React + TypeScript, WCAG AA
```
