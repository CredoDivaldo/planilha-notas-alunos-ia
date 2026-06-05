# Design Insights & Specification Directions

Baseadas em FR1-FR16 do PRD e journeys de usuários reais.

---

## 1. Arquitetura de Interfaces (Por Persona)

### Layout A: Professor (Desktop-first)
```
Header (logo + logout + contexto atual)
├─ Sidebar: Menu principal
│  ├─ Dashboard
│  ├─ Contextos académicos
│  ├─ Estudantes
│  ├─ Notas & Publicação
│  ├─ Auditoria
│  └─ Perfil
└─ Main: Conteúdo por secção
```

**Razão:** Professor precisa navegar entre várias operações (criar contexto, gerir estudantes, upload de notas, broadcast).

---

### Layout B: Estudante (Mobile-first)
```
Header (logo + logout + nome)
├─ Dashboard
│  ├─ Notas publicadas (cards por disciplina)
│  ├─ Calendário
│  ├─ Informações académicas
│  └─ Notificações
└─ Menu mínimo (avoid clutter)
```

**Razão:** Estudante usa primariamente mobile; interface deve ser leve e rápida.

---

### Layout C: Delegado (Desktop-friendly)
```
Header (logo + logout + nota: "Delegado de Turma A")
├─ Painel restrito
│  ├─ Lista de estudantes (turma própria)
│  ├─ Preparação de uploads (com "⏳ aguardando aprovação professor")
│  ├─ Auditoria da turma
│  └─ Perfil
└─ Main: Conteúdo
```

**Razão:** Delegado é estudante + ajudante técnico; precisa de interface simples mas com indicadores de permissões.

---

## 2. Interfaces Principais Necessárias

### Interface 1: Login Unificado (FR13)
**Users:** Professor, estudante, delegado  
**Fluxo:**
1. Email/número + senha
2. Se estudante (primeira vez): obriga troca de senha (FR13)
3. Se delegado detectado: oferece "Vista de Delegado" ou "Vista de Estudante"

**Design Points:**
- ✅ Claro qual papel vai usar
- ✅ Senha obrigatória na primeira vez
- ✅ Mensagem de erro explícita

---

### Interface 2: Dashboard Professor (FR2, FR3, FR4)
**User:** Professor  
**Conteúdo:**
- Lista de "Contextos activos hoje" com botão para alternar
- Botão "Novo contexto académico" (FR3)
- Atalhos para: Estudantes, Notas, Publicação, Auditoria
- Status rápido: "X estudantes inscritos, Y notas publicadas hoje"

**Design Points:**
- ✅ Contexto académico sempre visível (turma + disciplina + semestre + turno)
- ✅ Um clique para alternar entre contextos
- ✅ Números de operações (confiança)

---

### Interface 3: Criar Contexto Académico (FR3, FR4)
**User:** Professor  
**Fluxo:**
1. Modal/Wizard com etapas
2. Seleciona: Semestre → Turno → Turma → Disciplina
3. Validação em tempo real (ex: "Esta combo de turma + disciplina + semestre + turno já existe?")
4. Confirmação com preview
5. Salva e retorna a dashboard

**Design Points:**
- ✅ Etapas guiadas
- ✅ Validação clara
- ✅ Impossível criar contextos duplicados/inválidos

---

### Interface 4: Gestão de Estudantes (FR4, FR14)
**Users:** Professor, delegado (limitado)  
**Conteúdo:**
- Tabela com: número | nome | contacto (WhatsApp) | Delegado (checkbox)
- Botão "Upload CSV"
- Botão "Adicionar manual"
- Editar em linha (nome, contacto)
- Marcar como delegado (checkbox com confirmação)

**Upload Flow:**
1. Select arquivo CSV
2. Validação: duplicatas? Contactos inválidos? Números fora de faixa?
3. Preview: "vai importar 30 novos + atualizar 5 existentes"
4. Confirma
5. Relatório: "✅ 35 processados"

**Design Points:**
- ✅ Relatório de validação **antes** de persistir (FR4)
- ✅ Edição em linha para correções rápidas
- ✅ Delegado vê "⚠️ Precisa de confirmação do professor" quando tenta upload

---

### Interface 5: Upload & Gestão de Notas (FR5, FR6)
**User:** Professor (delegado pode preparar com confirmação)  
**Fluxo:**
1. Upload CSV com: número | nome | nota
2. Validação: correspondência com estudantes? Notas em faixa válida? Duplicatas?
3. Preview: "30 matched, 0 unmatched, 2 sem correspondência"
4. Opção: editar manualmente para unmatched (FR6)
5. Confirma
6. Notas ficar "em rascunho" (não publicadas ainda)

**Design Points:**
- ✅ Validação clara com relatório (FR5)
- ✅ Diferenciação entre "rascunho" e "publicado"
- ✅ Edição manual para correções (FR6)

---

### Interface 6: Publicação/Broadcast (FR9, FR10)
**User:** Professor  
**Fluxo:**
1. Dashboard ou contexto ativo mostra: "X notas em rascunho, prontas para publicação"
2. Clica "Publicar notas desta turma"
3. Modal confirma:
   - "Vai enviar para 30 estudantes via WhatsApp"
   - Preview da mensagem (ou template)
   - Opção: Dry-run (não enviar de verdade)
4. Confirma explicitamente: "Confirmo envio de verdade ✓"
5. Executa broadcast (cria snapshot publicado)
6. Relatório: "✅ Enviado para 30, 0 erros"

**Design Points:**
- ✅ Confirmação explícita antes de real (FR9)
- ✅ Dry-run para teste (FR9)
- ✅ Snapshot fica ligado ao broadcast (FR9)
- ✅ Novo broadcast possível se notas mudam (FR10)

---

### Interface 7: Portal do Estudante (FR12, FR13)
**User:** Estudante (autenticado)  
**Conteúdo:**
- Cards por disciplina: nome | nota (publicada) | data de publicação
- Seção "Informações Académicas": turma | curso | semestre | status
- Calendário: provas | exames | recursos (por data)
- Notificações: "Tua nota em Algoritmos foi publicada"

**Design Points:**
- ✅ Mobile-first (Ana acessa pelo celular)
- ✅ Apenas notas **publicadas** (não rascunho) (FR12)
- ✅ Data de publicação visível (rastreabilidade)
- ✅ Sem histórico detalhado visível (NFR8)

---

### Interface 8: Auditoria/Histórico (FR16)
**Users:** Professor, delegado (limitado)  
**Conteúdo:**
- Tabela com: data | operação (upload, publicação, edição) | quem (professor/delegado) | resultado
- Filtros: por data, por tipo de operação
- Para delegado: apenas da turma própria

**Design Points:**
- ✅ Rastreabilidade completa (FR16)
- ✅ Mostra claramente "quem fez"
- ✅ Delegado vê apenas ações da sua turma

---

### Interface 9: Painel do Delegado (FR14, FR15)
**User:** Delegado  
**Conteúdo:**
- Banner: "⚠️ Você é delegado de Turma A. Acesso limitado."
- Lista de estudantes (turma própria)
- Botão "Submeter upload de notas" (com status "⏳ aguardando aprovação")
- Auditoria da turma

**Design Points:**
- ✅ Permissões sempre visíveis
- ✅ Ações requerem confirmação do professor
- ✅ Não consegue fazer nada permanente sozinho

---

## 3. Padrões de Design

### Padrão 1: Confirmação Explícita
**Quando:** Ações que não podem ser revertidas (broadcast, atribuição de delegado)  
**Como:**
```
Modal com:
- Descrição do que vai acontecer
- Números (30 estudantes receberão mensagem)
- Opção de revisão (preview de dados)
- Botão vermelho "Confirmo esta ação"
```

---

### Padrão 2: Validação com Relatório
**Quando:** Uploads de CSV  
**Como:**
```
1. Validação silenciosa no backend
2. Mostrar relatório:
   - ✅ 28 registos OK
   - ⚠️ 2 contactos inválidos
   - ❌ 0 registos falhados
3. Preview dos dados antes de confirmar
4. Opção: "Revisar contactos inválidos"
```

---

### Padrão 3: Estado Visível
**Quando:** Qualquer operação longa ou assíncrona  
**Como:**
```
Mostrar sempre o estado:
- 📝 Rascunho (não publicado)
- ⏳ Processando upload
- ✅ Pronto
- 📤 Enviado
- ❌ Erro (com detalhes)
```

---

### Padrão 4: Restrições Visíveis
**Quando:** Delegado vê ações bloqueadas  
**Como:**
```
Botão desativado com tooltip:
"❌ Apenas o professor pode publicar.
Submeta este upload para aprovação."
```

---

## 4. Requisitos de Acessibilidade & Performance

**Acessibilidade (NFR6 - WCAG 2.2 AA):**
- ✅ Labels explícitos em todos os inputs
- ✅ Contraste mínimo AA
- ✅ Navegação por teclado funcional
- ✅ Aria-live para confirmações
- ✅ Alt text em imagens

**Performance:**
- ✅ Carregamento rápido em mobile (Ana usano celular)
- ✅ Uploads grandes devem mostrar barra de progresso
- ✅ Sem bloqueios de UI enquanto processa

---

## 5. Fluxos Críticos (Validação)

### Fluxo Crítico 1: Upload → Match → Publicação
```
Professor: 
  1. Upload CSV estudantes ✅
  2. Upload CSV notas ✅
  3. Sistema faz matching automático ✅
  4. Professor revisa ✅
  5. Professor publica (broadcast explícito) ✅
  6. Estudante vê notas publicadas ✅
```

**Design Checkpoint:** Cada etapa deve ser visível e confirmada.

---

### Fluxo Crítico 2: Delegado Ajuda com Aprovação
```
Delegado:
  1. Submete upload de estudantes/notas
  2. Status: "⏳ Aguardando aprovação" visível
Professor:
  3. Recebe notificação
  4. Revisa + aprova
  5. Upload processado
```

**Design Checkpoint:** Delegado nunca consegue fazer ação sensível sozinho.

---

## 6. Requisitos por Story

| Story | Interfaces Principais | Requisitos de UX |
|-------|--------------------|--------------------|
| **5.1** | Dashboard, Contextos | Visualizar modelo académico |
| **5.2** | Login, Perfil | Autenticação com papéis |
| **5.3** | Publicação/Broadcast | Confirmação explícita (FR9) |
| **5.4** | Contextos, Estudantes, Delegados | Criar contexto + atribuir delegado |
| **5.5** | Portal Estudante | Mobile-first, notas publicadas apenas |
| **6.1-6.3** | Chatbot (sem UI nova) | Webhook já implementado |

---

**Status:** ✅ Especificação pronta para wireframing  
**Próximo:** `*wireframe` com estas interfaces
