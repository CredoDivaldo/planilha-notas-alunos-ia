# Wireframe 001: Login Unificado (FR13)

**Fidelidade:** Low (ASCII)  
**User:** Professor, Estudante, Delegado  
**Requisitos:** FR13 (login + primeira troca obrigatória)

---

## Layout Principal

```
+─────────────────────────────────────────────┐
│                                             │
│         Planilha de Notas IA                │
│                                             │
+─────────────────────────────────────────────+

┌─────────────────────────────────────────────┐
│                                             │
│  Login                                      │
│  ═════════════════════════════════════════  │
│                                             │
│  Email / Número de Estudante:               │
│  ┌──────────────────────────────────────┐   │
│  │                                      │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Palavra-passe:                             │
│  ┌──────────────────────────────────────┐   │
│  │ ••••••••••••••••                      │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ⚠️  Email/número ou palavra-passe inválido │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │    Entrar                             │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  [ ] Lembrar-me                             │
│  Recuperar palavra-passe                    │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Estados

### Estado 1: Normal
- Email vazio
- Campo de palavra-passe
- Botão "Entrar" ativo

### Estado 2: Validação
- ✅ Email/número válido
- ✅ Palavra-passe preenchida
- Botão "Entrar" pronto

### Estado 3: Primeira Troca de Senha (Se aplicável)
```
┌─────────────────────────────────────────────┐
│                                             │
│  ⚠️  Primeira troca de palavra-passe        │
│                                             │
│  Por segurança, deve trocar a palavra-    │
│  passe padrão na primeira vez.             │
│                                             │
│  Palavra-passe actual:                      │
│  ┌──────────────────────────────────────┐   │
│  │ ••••••••••••••••                      │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  Nova palavra-passe:                        │
│  ┌──────────────────────────────────────┐   │
│  │                                      │   │
│  └──────────────────────────────────────┘   │
│  (mínimo 8 caracteres)                      │
│                                             │
│  Confirmar:                                 │
│  ┌──────────────────────────────────────┐   │
│  │                                      │   │
│  └──────────────────────────────────────┘   │
│                                             │
│  ┌──────────────────────────────────────┐   │
│  │    Confirmar Troca                    │   │
│  └──────────────────────────────────────┘   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Notas de Design

- ✅ Simples, sem distrações
- ✅ Labels explícitos
- ✅ Mensagem de erro clara se falhar
- ✅ Obrigatória troca no primeiro acesso (FR13)
- ✅ Modal para troca de senha (não deixa sair até trocar)

---

**Status:** ✅ Wireframe pronto  
**Próxima Interface:** Dashboard Professor
