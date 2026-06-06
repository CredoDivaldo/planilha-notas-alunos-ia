# Tela 00 — Login
**Viewport:** 1280px desktop | **Personas:** Professor, Estudante, Delegado

---

## Wireframe Mid-Fi

```
┌─────────────────────────────────────────────────────────────────────┐
│                          [1280px]                                    │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
│                                                                      │
│                    ┌──────────────────────────┐                     │
│                    │  📊 Planilha Notas       │                     │
│                    │  ── ── ── ── ── ── ──    │                     │
│                    │                          │                     │
│                    │  Entrar como             │                     │
│                    │  ┌─────────┐ ┌────────┐ │                     │
│                    │  │Professor│ │Estudnte│ │                     │
│                    │  └─────────┘ └────────┘ │                     │
│                    │                          │                     │
│                    │  ── ── [Professor] ── ── │                     │
│                    │                          │                     │
│                    │  Email / Utilizador      │                     │
│                    │  [Input: email@inst.ao ] │                     │
│                    │                          │                     │
│                    │  Palavra-passe           │                     │
│                    │  [Input: ············ ] │                     │
│                    │                          │                     │
│                    │  [     Entrar     ]      │                     │
│                    │                          │                     │
│                    │  ─────────────────────   │                     │
│                    │  Estudante? Use o número │                     │
│                    │  [Input: Nº Estudante ] │                     │
│                    │  [Input: Palavra-passe] │                     │
│                    │  [  Entrar como Aluno ] │                     │
│                    │                          │                     │
│                    │  ⚠️ Primeiro acesso?     │                     │
│                    │  Será pedida troca de    │                     │
│                    │  palavra-passe.          │                     │
│                    └──────────────────────────┘                     │
│                                                                      │
│  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Variante: Primeiro Acesso (Troca de Palavra-passe)

```
┌──────────────────────────┐
│  🔐 Primeiro Acesso       │
│  ── ── ── ── ── ── ──    │
│                           │
│  Bem-vindo, [Nome]!       │
│  Por segurança, defina    │
│  uma nova palavra-passe.  │
│                           │
│  Nova palavra-passe       │
│  [Input: ············ ] │
│                           │
│  Confirmar                │
│  [Input: ············ ] │
│                           │
│  ┌ ✅ min. 8 caracteres   │
│  └ ❌ letra maiúscula     │
│                           │
│  [  Definir e Entrar  ]  │
└──────────────────────────┘
```

---

## Anotações

| Elemento | Comportamento |
|----------|---------------|
| Tabs Professor/Estudante | Alterna forma de login; URL: `?role=professor` vs `?role=student` |
| Botão "Entrar" | Disabled até ambos os campos preenchidos |
| "Primeiro acesso" | Detectado pelo backend; redireciona para modal de troca |
| Validação inline | Erro aparece abaixo do campo com `aria-live="assertive"` |
| Focus order | Email → Senha → Botão entrar (tab natural) |

---

## Estados

- **Default:** formulário vazio, botão disabled
- **Loading:** botão com spinner "A entrar…"
- **Erro credenciais:** `⚠️ Email ou palavra-passe incorrectos.` abaixo do botão
- **Conta bloqueada:** `❌ Conta suspensa. Contacte o administrador.`

---

## AI Prompt (v0.dev)

```
Create a login page for an academic grade management system with:
- Centered card layout (max-width 440px) on a neutral gray background (#F8FAFC)
- Tab switcher: "Professor" | "Estudante" at the top of the card
- Professor form: email input + password input + primary "Entrar" button
- Student form: student number input + password input + primary "Entrar como Aluno" button
- Info text below student form: "Primeiro acesso? Será pedida troca de palavra-passe."
- Full WCAG AA compliance: visible focus rings, aria-label on inputs, error state with aria-live
- Color: Primary #0D6EFD, Error #B91C1C, background #F8FAFC
- Font: Inter, system-ui
- Framework: React + TypeScript + Tailwind CSS
- No logo image — use emoji 📊 + "Planilha Notas" as header
```
