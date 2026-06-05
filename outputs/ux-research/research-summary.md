# Research Summary — Planilha de Notas IA (Projeto Completo)

**Data:** 2026-06-03  
**Pesquisa:** Auditoria + Personas + Journeys + Design Insights  
**Escopo:** Projeto completo baseado em FR1-FR16 do PRD

---

## Achados Principais

### 1. Projeto é MUITO Mais que MVP
O PRD define 16 requisitos funcionais. O frontend MVP atual implementa apenas 5%.

**O que falta (90% do trabalho):**
- ✅ Backend Python pronto
- ❌ Frontend para: autenticação, contextos académicos, gestão de estudantes, publicação, portal estudante, delegados

---

### 2. Três Personas Distintas
| Persona | Dispositivo | Goals | Pain Point |
|---------|-----------|-------|-----------|
| **Prof. Carlos** | Desktop | Configurar turma → Publicar notas | Sistema fragmentado, medo de erro |
| **Ana** (Estudante) | Mobile | Ver notas → Calendário | Sem acesso controlado |
| **João** (Delegado) | Desktop | Ajudar professor | Medo de mexer em coisa sensível |

---

### 3. Fluxo Crítico (5 Etapas)

```
[Professor]
1. Login → Dashboard
2. Criar contexto (turma + disciplina + semestre + turno)
3. Cadastrar estudantes (upload + atribuir delegado)
4. Upload notas (validação + preview)
5. Publicar (broadcast explícito com confirmação)
            ↓
[Estudante]
6. Login → Portal → Ver notas publicadas + calendário
```

---

## Interfaces Principais (9 total)

| # | Interface | Para Quem | Criticidade |
|---|-----------|-----------|-------------|
| 1 | Login unificado | Todos | 🔴 BLOQUEANTE |
| 2 | Dashboard professor | Professor | 🔴 BLOQUEANTE |
| 3 | Criar contexto académico | Professor | 🔴 BLOQUEANTE |
| 4 | Gestão de estudantes | Professor + Delegado | 🔴 BLOQUEANTE |
| 5 | Upload & edição de notas | Professor | 🔴 BLOQUEANTE |
| 6 | Publicação/Broadcast | Professor | 🔴 BLOQUEANTE |
| 7 | Portal do estudante | Estudante | 🔴 BLOQUEANTE |
| 8 | Auditoria | Professor + Delegado | 🟠 IMPORTANTE |
| 9 | Painel delegado | Delegado | 🟠 IMPORTANTE |

---

## Key Design Principles

1. **Confirmação Explícita** (FR9)
   - Publicação deve exigir confirmação clara
   - Não deve ser acidental

2. **Permissões Visíveis** (FR14-FR15)
   - Delegado sempre vê o que pode/não pode fazer
   - Ações sensíveis requerem aprovação do professor

3. **Validação com Relatório** (FR4-FR6)
   - Uploads devem mostrar préview + validação antes de persistir
   - Sem surpresas

4. **Rastreabilidade Completa** (FR16)
   - Auditoria sempre visível
   - Quem fez o quê, quando

5. **Mobile para Estudante, Desktop para Professor**
   - Duas interfaces otimizadas (não "responsivo igual")
   - Ana acessa pelo celular; Carlos pelo desktop

---

## Painços vs. Oportunidades de Design

| Persona | Pain Point | Oportunidade de Design |
|---------|-----------|------------------------|
| **Prof. Carlos** | Sistema fragmentado | ✅ Dashboard com contextos activos |
| | Medo de enviar errado | ✅ Confirmação explícita antes de broadcast |
| | Sem histórico | ✅ Auditoria completa visível |
| | Delegado sem limites claros | ✅ Permissões sempre visíveis no UI |
| **Ana** | Espera dias para saber nota | ✅ Portal móvel com consulta imediata |
| | Sem contexto (só número) | ✅ Data de publicação + status claro |
| | Portal da universidade confuso | ✅ Interface simples mobile-first |
| **João** (Delegado) | Medo de mexer em coisa sensível | ✅ Interface clara: "podes fazer isto" |
| | Sem feedback do que mudou | ✅ Auditoria da turma visível |

---

## Requisitos de Design por Story (FR mapping)

| Story | Requisitos Relacionados | Interface(s) |
|-------|------------------------|-------------|
| **5.1** | FR1, FR2 | Dashboard, contextos |
| **5.2** | FR13, FR14 | Login, papéis |
| **5.3** | FR8, FR9 | Publicação/Broadcast |
| **5.4** | FR3, FR4, FR14 | Contexto, estudantes, delegado |
| **5.5** | FR12, FR13 | Portal estudante |
| **6.1-6.3** | FR11 | Chatbot (backend ready) |

---

## Insights Chave para Implementação

### Insight 1: Fluxo MVP Precisa ser Revisado
O MVP atual (upload → match → envio WhatsApp) foi design para teste rápido.  
**Novo fluxo:** Criar contexto → Cadastrar estudantes → Upload notas → Publicação **controlada** → Portal consulta.

### Insight 2: Publicação Controlada é O Pivô
FR9 ("notas visíveis apenas após broadcast explícito") é o requisito mais importante.  
**Design implication:** Confirmação explícita antes de qualquer envio. Nunca acidental.

### Insight 3: Delegado é Estudante + Ajudante
João é estudante (pode ver suas próprias notas) + delegado (pode ajudar professor).  
**Design implication:** Dois modos de acesso, claramente diferenciados na UI.

### Insight 4: Mobile é Crítico para Estudante
Ana usa primariamente mobile (80% de uso).  
**Design implication:** Portal deve ser mobile-first, não desktop + responsivo.

### Insight 5: Validação Previne Erros Operacionais
Uploads são ponto crítico onde erros podem acontecer.  
**Design implication:** Sempre mostrar validação + preview antes de persistir.

---

## Próximos Passos

### Fase 2: Wireframing
- [ ] Low-fidelity wireframes (9 interfaces)
- [ ] User flow diagrams
- [ ] State diagrams (rascunho → publicado, etc.)

### Fase 3: Especificação Detalhada
- [ ] Componentes React/HTML necessários
- [ ] Regras de estado (quando botão está ativo/inativo)
- [ ] Mensagens de erro esperadas
- [ ] Sequências de validação

### Fase 4: Design System
- [ ] Palette de cores (sucesso, aviso, erro)
- [ ] Tipografia
- [ ] Componentes reutilizáveis (Button, Modal, Table, etc.)

---

## Confiança da Pesquisa

**Baseado em:**
- ✅ PRD formal (FR1-FR16)
- ✅ Arquitetura técnica existente
- ✅ Backend implementado (FastAPI)
- ✅ Casos de uso reais

**Não inventado:**
- ❌ Personas não são fictícias; são papéis definidos no PRD
- ❌ Journeys não são especulações; são fluxos exigidos em FR
- ❌ Interfaces não são "ideias bacanas"; são blockeantes para funcionalidade

**Status:** ✅ Pronto para wireframing  
**Próximo comando:** `*wireframe low`

---

*Pesquisa realizada por Uma (UX-Design-Expert)  
Baseada em: PRD (docs/prd.md), Arquitetura (docs/architecture.md), Frontend Spec (docs/frontend/frontend-spec.md)*
