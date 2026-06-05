# Auditoria UX — Planilha de Notas IA

**Data:** 2026-06-03  
**Realizado por:** Uma (UX-Design-Expert)  
**Escopo:** Inventário de interfaces necessárias vs. implementadas

---

## 1. Backend Implementado (Python/FastAPI)

✅ **Modelagem Académica:**
- Semestres, turnos, turmas, disciplinas
- Professores, estudantes, delegados
- Alocações docentes (TeachingAssignment)
- Matrículas (Enrollment)

✅ **Autenticação & Papéis:**
- Login estudante (número + senha)
- Primeira troca obrigatória de senha
- Papéis: professor, delegado, estudante
- Gestão de sessões

✅ **Publicação de Notas:**
- Distinguir notas internas vs. publicadas
- Snapshots de publicação
- Broadcast manual como gatilho

✅ **Portal do Estudante (Read Model):**
- Leitura de notas publicadas
- Informações académicas visíveis
- Protegido por autenticação

✅ **Chatbot AI:**
- Webhook WhatsApp (Evolution API)
- Serviço IA (Baidu QianFan)
- Responde sobre notas publicadas

---

## 2. Frontend Atual (MVP Simples)

✅ **Página única com 5 etapas:**
1. Upload de estudantes (CSV)
2. Upload de notas (CSV)
3. Gerar match
4. Conectar WhatsApp (Evolution)
5. Enviar mensagem em massa

⚠️ **Limitações:**
- Sem autenticação
- Sem modelo académico visível
- Sem contexto de turma/disciplina/semestre
- Sem portal do estudante
- Sem gestão de papéis

---

## 3. Interfaces NECESSÁRIAS (mas não implementadas)

### A. Contexto Académico (Professor)
**Necessário para:** Story 5.4  
**O que falta:**
- ❌ Interface para criar/selecionar semestre
- ❌ Interface para criar/selecionar turno
- ❌ Interface para criar/selecionar turma
- ❌ Interface para associar disciplina
- ❌ Interface para associar professores à turma
- **Impacto:** SEM ISTO, professor não consegue criar contexto operacional

### B. Gestão de Estudantes (Professor + Delegado)
**Necessário para:** Story 5.1, 5.2, 5.4  
**O que falta:**
- ❌ Upload CSV com estudantes + dados básicos
- ❌ Edição manual de estudante
- ❌ Atribuição de delegado (selecionar estudante → marcar como delegado)
- ❌ Geração de senha inicial
- ❌ Lista de estudantes por turma
- **Impacto:** SEM ISTO, estudantes não conseguem fazer login

### C. Autenticação (Todas as personas)
**Necessário para:** Stories 5.1-5.5, 6.x  
**O que falta:**
- ❌ Página de login (professor, estudante, delegado)
- ❌ Validação de credenciais
- ❌ Gestão de sessão
- ❌ Logout
- ❌ Primeira troca obrigatória de senha
- ❌ Recovery de senha (possível feature futura)
- **Impacto:** SEM ISTO, ninguém consegue aceder ao sistema securo

### D. Portal do Estudante
**Necessário para:** Story 5.5, 6.x  
**O que falta:**
- ❌ Dashboard do estudante (autenticado)
- ❌ Vista de notas publicadas
- ❌ Informações académicas (turma, curso, estado)
- ❌ Calendário de provas/exames/recursos
- ❌ Interface mobile-first
- **Impacto:** SEM ISTO, estudante não consegue consultar notas (apenas via WhatsApp)

### E. Gestão de Publicação (Professor)
**Necessário para:** Story 5.3  
**O que falta:**
- ❌ Interface para visualizar notas internas
- ❌ Interface para confirmar publicação (broadcast)
- ❌ Histórico de broadcasts realizados
- ❌ Novo broadcast se notas forem alteradas
- **Impacto:** SEM ISTO, notas publicadas não são visíveis de forma controlada

### F. Painel Operacional do Professor (Revisado)
**Necessário para:** Integração de todas as stories  
**O que falta:**
- ❌ Dashboard com contextos académicos ativos
- ❌ Rota para upload de notas → match → publicação (não apenas envio WhatsApp)
- ❌ Visualização de estado (notas internas vs. publicadas)
- ❌ Suporte a delegado com permissões limitadas
- **Impacto:** SEM ISTO, professor não vê toda a operação

### G. Gestão de Delegado (Professor)
**Necessário para:** Story 5.2, 5.4  
**O que falta:**
- ❌ Interface para atribuir delegado a uma turma
- ❌ Vista de permissões do delegado
- ❌ Bloqueio de ações sensíveis (professor precisa confirmar)
- ❌ Auditoria de ações do delegado
- **Impacto:** SEM ISTO, delegado não consegue ajudar de forma segura

---

## 4. Matriz de Interfaces vs. Stories

| Interface | Story | Implementada | Status |
|-----------|-------|--------------|--------|
| Login professor | 5.2 | ❌ | Bloqueante |
| Login estudante | 5.2 | ❌ | Bloqueante |
| Contexto académico (criar/selecionar) | 5.4 | ❌ | Bloqueante |
| Gestão de estudantes | 5.1 | ❌ | Bloqueante |
| Atribuição de delegado | 5.2 | ❌ | Bloqueante |
| Dashboard estudante | 5.5 | ❌ | Bloqueante |
| Publicação/Broadcast | 5.3 | ❌ | Bloqueante |
| Painel professor | 5.4 | ⚠️ Parcial | Precisa redesign |
| Chatbot AI | 6.x | ✅ (backend) | Pronto (sem UI) |

---

## 5. Impacto da Falta de UX

**Problema:** O PRD define 16 requisitos funcionais (FR1-FR16). O frontend MVP implementa apenas ~5% deles.

**Consequência:** 
- Estudantes não conseguem fazer login
- Professores não conseguem criar contextos académicos
- Delegados não conseguem ser atribuídos
- Notas não conseguem ser publicadas de forma controlada
- Portal do estudante não existe

**Resultado:** Backend bonito sem nenhuma forma de acesso = produto inutilizável

---

## 6. Recomendação Estratégica

Você precisa de **múltiplos ecrãs/interfaces**, organizados por persona:

### **Fluxo Professor (Desktop-first):**
1. Login professor
2. Dashboard com contextos académicos ativos
3. Criar/editar contexto (turma, disciplina, semestre, turno)
4. Gestão de estudantes (upload, edição, delegados)
5. Upload de notas (ainda ao modelo MVP)
6. Publicação/Broadcast (novo)
7. Auditoria/Histórico (futuro)

### **Fluxo Estudante (Mobile-first):**
1. Login estudante (número + senha)
2. Primeira troca obrigatória de senha
3. Dashboard: notas publicadas + calendário
4. Consulta de informações académicas

### **Fluxo Delegado (Desktop-friendly):**
1. Login como estudante
2. Vista restrita a turma própria
3. Ajuda em uploads/preparação (com aprovação professor)

---

## 7. Próximos Passos para UX

**Recomendação:** 
A pesquisa de UX deve mapear **TODAS as interfaces necessárias** e criar **especificação de fluxos por persona**, não apenas o MVP simples.

Isto significa:
1. Personas: Professor, Estudante, Delegado (não apenas "Maria" e "Lucas")
2. Journeys: Contexto académico → Estudantes → Publicação → Consulta
3. Wireframes: ~6-8 interfaces principais
4. Specification: Um documento que diga "isto é o que o frontend deve fazer para cada história 5.x e 6.x"

---

**Status:** Auditoria completa  
**Conclusão:** Projeto é maior do que o MVP simples
