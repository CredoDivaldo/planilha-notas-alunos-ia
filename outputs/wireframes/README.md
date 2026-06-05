# Wireframes — Planilha de Notas IA

**Fidelidade:** Low (ASCII/Text-based)  
**Status:** ✅ COMPLETO (9/9 interfaces)  
**Data:** 2026-06-03

---

## 📋 Interface Map

```
001 — Login Unificado (FR13)
     ├─ Professor
     ├─ Estudante (+ primeira troca obrigatória)
     └─ Delegado

002 — Dashboard Professor (FR2-FR3)
      ├─ Contextos activos com selector
      ├─ Status rápido
      └─ Atalhos para operações

003 — Criar Contexto Académico (FR3-FR4)
      ├─ Wizard 4 etapas (semestre → turno → turma → disciplina)
      ├─ Validação em tempo real
      └─ Confirmação com preview

004 — Gestão de Estudantes (FR4, FR14)
      ├─ Upload CSV com validação
      ├─ Edição em linha
      ├─ Atribuição de delegado
      └─ Relatório de validação

005 — Upload & Edição de Notas (FR5-FR6)
      ├─ Upload CSV com validação
      ├─ Edição em linha
      ├─ Adicionar manual
      └─ Estados: matched ✅ | sem nota ⚠️ | unmatched ❌

006 — Publicação/Broadcast (FR9-FR10) 🔴 CRÍTICO
      ├─ Confirmação explícita obrigatória
      ├─ Dry-run para simulação
      ├─ Botão vermelho para acção final
      └─ Novo broadcast se houver alterações

007 — Portal Estudante (FR12)
      ├─ Mobile-first (primário)
      ├─ Cards por disciplina (notas publicadas)
      ├─ Calendário de avaliações
      ├─ Informações académicas
      └─ Notificações de publicação

008 — Auditoria (FR16)
      ├─ Histórico de operações (data | operação | quem | resultado)
      ├─ Filtros por data, operação, autor
      ├─ Detalhes de cada operação
      └─ Exportação PDF

009 — Painel Delegado (FR14-FR15)
      ├─ Dashboard com restrições visíveis
      ├─ Gestão estudantes (com aprovação professor)
      ├─ Upload com submissão (não directo)
      ├─ Ações bloqueadas com feedback claro
      └─ Auditoria limitada à turma própria
```

---

## 🎯 Requisitos Mapeados

| FR | Requisito | Interface |
|----|-----------|-----------|
| FR1 | Preservar fluxo MVP | Todas (integrado) |
| FR2 | Gestão semestres, turmas, disciplinas | 002-003 |
| FR3 | Múltiplos contextos professor | 002-003 |
| FR4 | Cadastro estudantes | 003-004 |
| FR5 | Importação CSV notas | 005 |
| FR6 | Edição manual notas | 005 |
| FR7 | Cálculo (backend, sem UI) | — |
| FR8 | Dados internos vs publicados | 005-006 |
| FR9 | Publicação por broadcast explícito | 006 🔴 |
| FR10 | Novo broadcast se alterações | 006 |
| FR11 | WhatsApp como canal | (backend) |
| FR12 | Portal estudante | 007 |
| FR13 | Login + primeira troca senha | 001 |
| FR14 | Permissões delegado | 004, 009 |
| FR15 | Bloqueio ações sensíveis | 009 |
| FR16 | Auditoria operacional | 008 |

---

## 🔴 Wireframes Críticos

Estes wireframes implementam requisitos **bloqueantes** (não funciona sem eles):

1. **006 — Publicação/Broadcast (FR9)**
   - Confirmação explícita obrigatória
   - Botão vermelho para acção final
   - Impossível enviar acidentalmente

2. **001 — Login (FR13)**
   - Autenticação para todos os papéis
   - Primeira troca obrigatória no acesso inicial

3. **004-005 — Gestão Dados (FR4-FR6)**
   - Validação em tempo real
   - Preview antes de persistir

---

## 📐 Padrões de Design

### Padrão 1: Confirmação Explícita
Usado em: **006 (Broadcast)**
```
Normal Modal → Simulação → Confirmação Final (botão vermelho)
```

### Padrão 2: Validação com Relatório
Usado em: **004-005 (Uploads)**
```
Upload → Validação silenciosa → Relatório com detalhes → Confirmar
```

### Padrão 3: Permissões Visíveis
Usado em: **009 (Delegado)**
```
Ações bloqueadas sempre explicam o porquê
Contacto do professor disponível
```

### Padrão 4: Status Sempre Claro
Usado em: **todas**
```
Estado visível em cada operação (rascunho, processando, sucesso, erro)
```

---

## 🎬 User Flows Representados

### Flow 1: Professor — Create Context → Upload Students → Upload Notes → Publish
```
002 → 003 → 004 → 005 → 006
```

### Flow 2: Estudante — Login → View Notas → Check Calendar
```
001 → 007
```

### Flow 3: Delegado — Login → Prepare Upload → Submit for Approval
```
001 → 009 → 004 (submit flow)
```

---

## ✅ Design Checklist

- ✅ 9 interfaces covering all FR1-FR16
- ✅ Confirmações explícitas onde necessário (FR9)
- ✅ Permissões sempre visíveis (FR14-FR15)
- ✅ Validação com relatório (FR4-FR6)
- ✅ Mobile-first para estudante, desktop para professor
- ✅ Rastreabilidade completa (FR16)
- ✅ Estados sempre claros (rascunho vs publicado)
- ✅ Nenhuma operação sensível é acidental

---

## 📝 Notas para Desenvolvimento (@dev)

1. **Prioridade 1 (Bloqueante):**
   - 001 Login + primeira troca senha
   - 006 Publicação com confirmação explícita
   - 004 Upload estudantes com validação

2. **Prioridade 2 (Completar core):**
   - 002-003 Dashboard + contexto
   - 005 Upload notas
   - 007 Portal estudante

3. **Prioridade 3 (Nice-to-have):**
   - 008 Auditoria
   - 009 Painel delegado completo

---

## 🚀 Próximos Passos

1. **Design System** — Cores, tipografia, componentes reutilizáveis
2. **Mid-Fi Mockups** — Refinar layouts com mais detalhes
3. **User Testing** — Validar com professor real (Carlos) + estudante (Ana)
4. **Hi-Fi Design** — Produção ready para handoff a @dev
5. **Specification Detalhada** — Por interface, com mensagens de erro, estados, etc.

---

**Status:** ✅ Low-Fidelity Wireframes COMPLETE  
**Confiança:** HIGH (100% baseado em FR do PRD)  
**Pronto para:** Mid-Fi design ou development kickoff

---

*Criado por Uma (UX-Design-Expert) em 2026-06-03*
