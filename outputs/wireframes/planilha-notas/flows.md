# Fluxos de Interacção — Planilha Notas
**Gerado por:** Uma (UX-Design Expert) | **Data:** 2026-06-05

---

## Fluxo Principal: Professor — Upload → Match → Publicar

```
[Login Professor]
        ↓
[Painel Operacional]
        ↓
    ┌───────────────────────────────────────────┐
    │  STEP 1: Upload Estudantes CSV             │
    │  POST /api/students/upload                 │
    │  ✅ → studentsStatus "142 carregados"       │
    │  ❌ → erro inline no StepCard              │
    └───────────────────────────────────────────┘
        ↓
    ┌───────────────────────────────────────────┐
    │  STEP 2: Upload Notas CSV                  │
    │  POST /api/grades/upload                   │
    │  ✅ → gradesStatus "138 notas importadas"  │
    └───────────────────────────────────────────┘
        ↓
    ┌───────────────────────────────────────────┐
    │  STEP 3: Gerar Match                       │
    │  POST /api/match/generate                  │
    │  ✅ → tabela match + stats                 │
    │  ❌ → matchStats com erro                  │
    └───────────────────────────────────────────┘
        ↓
    ┌───────────────────────────────────────────┐
    │  STEP 4: Conectar WhatsApp                 │
    │  Criar instância → QR → Verificar          │
    │  ✅ → badge verde "Conectado"              │
    │  ⏱  QR expira 45s → gerar novo            │
    └───────────────────────────────────────────┘
        ↓
    ┌───────────────────────────────────────────┐
    │  STEP 5: Disparar Mensagens                │
    │  Modo: DryRun | Envio Real                 │
    │  DryRun → simulação sem envio              │
    │  Envio Real → modal de confirmação (4.6)   │
    │  POST /api/send/bulk                       │
    │  ✅ → summary + resultados                 │
    └───────────────────────────────────────────┘
        ↓
  [Alternativa: Fluxo de Publicação (Tela 07)]
```

---

## Fluxo: Publicação de Notas (Tela 07)

```
[Notas completas em Gestão de Notas]
        ↓
[Clicar "Publicar notas"]
        ↓
  ┌─────────────────┐
  │ Passo 1: Revisão│ — verificar notas, alertas de incompletos
  └─────────────────┘
        ↓
  ┌────────────────────┐
  │ Passo 2: Audiência │ — todos / aprovados / reprovados / manual
  └────────────────────┘
        ↓
  ┌──────────────────┐
  │ Passo 3: Canais  │ — WhatsApp / Email / Só portal
  └──────────────────┘
        ↓
  ┌──────────────────────┐
  │ Passo 4: Confirmar   │ — checkbox obrigatório + "Publicar"
  └──────────────────────┘
        ↓
  ┌─────────────────────────────┐
  │ Resultado: Stats + Falhas   │
  │ [Re-enviar falhados] se > 0 │
  └─────────────────────────────┘
        ↓
[Portal do Estudante actualizado — notas visíveis]
```

---

## Fluxo: Login e Primeiro Acesso

```
[/login]
    ↓
[Seleccionar: Professor | Estudante]
    ↓ Professor                ↓ Estudante
[Email + Senha]          [Nº Estudante + Senha]
    ↓                          ↓
[POST /auth/login]       [POST /auth/login]
    ↓                          ↓
[Primeiro acesso?]       [Primeiro acesso?]
    ↓ Sim      ↓ Não       ↓ Sim      ↓ Não
[Troca senha]  [Painel]   [Troca senha]  [Portal]
    ↓                          ↓
[Painel Prof.]             [Portal Estudante]
```

---

## Fluxo: Estudante — Consultar Notas

```
[Login Estudante]
        ↓
[Portal do Estudante]
        ↓
[Notas visíveis?]
    ↓ Sim                        ↓ Não
[Ver notas publicadas]    [Mensagem: "ainda não publicadas"
[Componentes + Final]      + notificação via WhatsApp]
[Resultado badge]
        ↓
[Calendário de eventos]
        ↓
[Chatbot WhatsApp (Epic 6)]
```

---

## Fluxo: Chatbot WhatsApp (Epic 6)

```
[Estudante envia mensagem WhatsApp]
        ↓
[Webhook Evolution API recebe]
POST /api/chatbot/webhook
        ↓
[Identificar estudante por número de telefone]
    ↓ Encontrado        ↓ Não encontrado
[Consultar notas         [Responder: "número
 publicadas do aluno]     não reconhecido"]
        ↓
[LLM interpreta pergunta em linguagem natural]
        ↓
[Notas publicadas? (FR9)]
    ↓ Sim                    ↓ Não
[Responder com          [Responder: "notas
 dados publicados]       ainda não publicadas"
                         (FR20)]
        ↓
[Enviar resposta via Evolution API]
```

---

## Fluxo: Delegado

```
[Login Delegado]
        ↓
[Vista Técnica Delegado]  ← read-only
        ↓
[Ver estudantes da turma]
[Ver notas publicadas]
[Exportar CSV da turma]
        ↓
[Identificar contactos com problema]
[Comunicar ao professor]  ← fora do sistema
```
