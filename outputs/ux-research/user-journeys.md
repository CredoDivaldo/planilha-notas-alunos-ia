# User Journeys — Planilha de Notas IA (Projeto Completo)

Baseados em FR1-FR16 e workflows reais de cada persona.

---

## Journey 1: Prof. Carlos — "Configurar Turma e Publicar Notas"

**Cenário:** Carlos leciona "Algoritmos" em "Turma A" do "Semestre 2026.1 Manhã". Precisa importar 30 estudantes, fazer upload de notas e publicar.

### Stage 1: Login & Dashboard

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Abre aplicação, faz login com email/senha do professor |
| **Pensamento** | "Tenho 5 disciplinas, qual é a ativa hoje?" |
| **Emoção** | 😐 Neutro, funcional |
| **Pain Point** | ❌ Sem feedback visual do contexto selecionado |
| **Oportunidade** | ✅ Dashboard mostra: "Contextos ativos hoje" com lista |

**Design Implication:** Dashboard deve mostrar **contextos ativos** (turma + disciplina + semestre) com seletor para alternar entre eles (FR3).

---

### Stage 2: Criar Novo Contexto (Se Necessário)

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Se primeira vez: clica "Novo contexto académico" |
| **Sub-ações** | Seleciona semestre → turno → turma → disciplina → confirma |
| **Pensamento** | "Espero que isto fique certo da primeira vez" |
| **Emoção** | 😐 Preocupado com erros |
| **Pain Point** | ❌ Sem validação de combos inválidos (ex: turma sem turno) |
| **Oportunidade** | ✅ Validação em tempo real, preview antes de confirmar |

**Design Implication:** Interface de criação de contexto deve ser **guiada por etapas** com validação clara (FR4 + FR3).

---

### Stage 3: Gestão de Estudantes

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Upload CSV com nome + número + contacto (WhatsApp) |
| **Sub-ações** | Validação de ficheiro → preview → confirma importação |
| **Pensamento** | "Os dados estão certos? Há duplicatas?" |
| **Emoção** | 😐 Ansioso, quer validação |
| **Pain Point** | ❌ Sem detecção de erros (números duplicados, contactos inválidos) |
| **Oportunidade** | ✅ Relatório de validação antes de import (FR4) |

**Design Implication:** Upload deve ter **preview + validação** antes de persistir (FR4, FR5).

---

### Stage 4: Atribuir Delegado (Novo)

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Na lista de estudantes, seleciona um e marca como "Delegado" |
| **Pensamento** | "João é confiável, vou deixá-lo ajudar" |
| **Emoção** | 😊 Confiante com a delegação |
| **Pain Point** | ❌ Sem interface visual para isto (não existe ainda) |
| **Oportunidade** | ✅ Checkbox "Delegado" na lista de estudantes + confirmação |

**Design Implication:** Atribuição de delegado deve ser **simples e visível** na lista (FR14).

---

### Stage 5: Upload de Notas

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Upload CSV com número + nome + nota |
| **Sub-ações** | Validação → preview → confirma |
| **Pensamento** | "Espero que isto combine com os estudantes" |
| **Emoção** | 😐 Nervoso com matching |
| **Pain Point** | ❌ Sem feedback sobre "matched" vs "unmatched" (não existe ainda) |
| **Oportunidade** | ✅ Relatório: "30 estudantes matched, 0 unmatched, 2 notas sem correspondência" |

**Design Implication:** Upload deve ter **relatório detalhado de validação** (FR5, FR6).

---

### Stage 6: Publicação/Broadcast (Novo)

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Clica "Publicar notas" → confirmação explícita → broadcast executado |
| **Sub-ações** | Revisa lista de estudantes que receberão mensagem → confirma → enviado |
| **Pensamento** | "Preciso ter certeza antes de enviar de verdade" |
| **Emoção** | 😟 Preocupado com erros, quer confirmação |
| **Pain Point** | ❌ MVP atual não tem broadcast controlado (envia direto) |
| **Oportunidade** | ✅ Confirmação explícita com preview + dry-run opcional (FR9, FR10) |

**Design Implication:** Broadcast deve ter **confirmação visual explícita** antes de envio real (FR9).

---

### Stage 7: Auditoria (Novo)

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Vê histórico: uploads, broadcasts, alterações |
| **Pensamento** | "Quando foi que a última publicação foi feita?" |
| **Emoção** | 😊 Seguro com rastreabilidade |
| **Pain Point** | ❌ Sem histórico visível (não existe) |
| **Oportunidade** | ✅ Log mostra: data, quem (professor/delegado), o quê, resultado |

**Design Implication:** Dashboard deve incluir **auditoria de operações** (FR16).

---

## Journey 2: Ana — "Consultar Notas no Portal"

**Cenário:** Ana quer saber suas notas após professor fazer broadcast. Acessa pelo celular enquanto viaja.

### Stage 1: Login Móvel

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Abre site/app no celular, faz login (número + senha) |
| **Pensamento** | "Espero que isto carregue rápido" |
| **Emoção** | 😐 Impaciente |
| **Pain Point** | ❌ Portal não existe (FR12) |
| **Oportunidade** | ✅ Interface mobile-first, carregamento rápido |

**Design Implication:** Portal deve ser **mobile-first, responsivo, rápido** (FR12, NFR6).

---

### Stage 2: Primeira Troca de Senha

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Se primeira vez: obrigado a trocar senha padrão |
| **Pensamento** | "Certa, deixa-me criar uma segura" |
| **Emoção** | 😐 Neutro, procedimento |
| **Pain Point** | ❌ Interface para isto não existe |
| **Oportunidade** | ✅ Diálogo claro: "Tua senha padrão. Cria nova agora." (FR13) |

**Design Implication:** Modal de troca de senha obrigatória deve ser **claro e não-invasivo** (FR13).

---

### Stage 3: Dashboard — Ver Notas Publicadas

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Dashboard mostra notas por disciplina (apenas publicadas) |
| **Sub-ações** | Clica em disciplina para ver detalhe |
| **Pensamento** | "Qual é minha nota em Algoritmos?" |
| **Emoção** | 😟 Ansiosa para ver |
| **Pain Point** | ❌ Sem interface de consulta (não existe) |
| **Oportunidade** | ✅ Cards por disciplina: nome + nota + data de publicação |

**Design Implication:** Dashboard deve mostrar **notas por disciplina com data de publicação** (FR12, FR9).

---

### Stage 4: Informações Académicas

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Vê turma, curso, semestre, estado académico |
| **Pensamento** | "Qual é meu estado nesta disciplina?" |
| **Emoção** | 😊 Informada, segura |
| **Pain Point** | ❌ Sem contexto académico visível |
| **Oportunidade** | ✅ Seção: "Informações Académicas" com status e calendário |

**Design Implication:** Dashboard deve mostrar **contexto académico + calendário** (FR12).

---

### Stage 5: Calendário (Futuro)

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Vê provas, exames, recursos da semana/mês |
| **Pensamento** | "Quando é a prova de Algoritmos?" |
| **Emoção** | 😊 Organizada |
| **Pain Point** | ❌ Sem calendário visível |
| **Oportunidade** | ✅ Seção "Calendário": eventos por data |

**Design Implication:** Portal deve incluir **calendário de avaliações** (FR12).

---

## Journey 3: João — "Ajudar Professor como Delegado"

**Cenário:** João (delegado) ajuda Prof. Carlos com upload de notas, mas não quer mexer em tudo.

### Stage 1: Login como Delegado

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Faz login como estudante (número + senha) |
| **Sub-ações** | Sistema detecta que é delegado → oferece "Vista de Delegado" |
| **Pensamento** | "Qual é meu acesso hoje?" |
| **Emoção** | 😐 Cuidadoso, quer saber limites |
| **Pain Point** | ❌ Sem interface que mostre permissões |
| **Oportunidade** | ✅ Banner claro: "Você é delegado de Turma A. Acesso limitado." |

**Design Implication:** Dashboard delegado deve mostrar **permissões explicitamente** (FR14).

---

### Stage 2: Painel Restrito à Turma

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Vê apenas lista de estudantes de sua turma |
| **Pensamento** | "Posso ver os estudantes, mas não posso mexer em outras turmas" |
| **Emoção** | 😊 Seguro dentro do escopo |
| **Pain Point** | ❌ Sem interface de delegado |
| **Oportunidade** | ✅ Painel mostra: turma + estudantes + permissões |

**Design Implication:** Delegado vê **apenas sua turma, sem acesso a outras** (FR14, FR15).

---

### Stage 3: Ajuda em Uploads (Com Confirmação)

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Upload de notas CSV, mas precisa de confirmação do professor |
| **Sub-ações** | Submete → professor recebe notificação → aprova/rejeita |
| **Pensamento** | "O professor vai revisar antes de publicar, certo?" |
| **Emoção** | 😊 Confiante porque há revisão |
| **Pain Point** | ❌ Sem workflow de aprovação |
| **Oportunidade** | ✅ Fluxo: delegado submete → professor aprova (FR15) |

**Design Implication:** Ações do delegado devem ter **confirmação do professor** (FR15).

---

### Stage 4: Ver Auditoria da Turma

| Componente | Detalhe |
|-----------|---------|
| **Ação** | Vê histórico de uploads/broadcasts da turma |
| **Pensamento** | "Quem fez o upload? Quando?" |
| **Emoção** | 😊 Informado |
| **Pain Point** | ❌ Sem auditoria visível |
| **Oportunidade** | ✅ Log da turma: operações + quem as fez |

**Design Implication:** Delegado pode ver **auditoria limitada à sua turma** (FR16).

---

## Insights Críticos (Baseados no PRD)

### Insight 1: Publicação Controlada é Crítica (FR9)
**Evidência:** PRD exigir "broadcast explícito" como gatilho de publicação  
**Design Need:** Não deve ser acidental; confirmação visual obrigatória  

### Insight 2: Papéis Precisam Ser Visíveis (FR14, FR15)
**Evidência:** Delegado não pode mexer em coisas sensíveis  
**Design Need:** Interface deve mostrar sempre: "tu podes fazer isto, não aquilo"  

### Insight 3: Auditoria é Confiança (FR16)
**Evidência:** Validação que "quem fez o quê, quando"  
**Design Need:** Log sempre visível para professor + delegado  

### Insight 4: Mobile para Estudante, Desktop para Professor
**Evidência:** Ana acessa pelo celular; Carlos pelo desktop  
**Design Need:** Duas interfaces otimizadas (não "responsivo igual")  

### Insight 5: Validação Previne Erros (FR5, FR6)
**Evidência:** Uploads devem validar antes de persistir  
**Design Need:** Preview + relatório detalhado antes de confirmar  

---

**Status:** ✅ Baseados em FR1-FR16 do PRD  
**Cobertura:** Professor + Estudante + Delegado
