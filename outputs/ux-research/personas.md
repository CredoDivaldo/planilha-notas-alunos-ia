# Personas — Planilha de Notas IA (Projeto Completo)

Personas baseadas em FR1-FR16 do PRD e casos de uso reais.

---

## Persona 1: Prof. Carlos — Professor Operacional

**Demographics:**
- Idade: 38 anos
- Experiência: 12 anos lecionando
- Tech level: Intermédio (email, spreadsheets, navegadores)
- Contexto: Leciona 5 disciplinas em 3 semestres simultâneos

**Goals:**
- ✅ Configurar rapidamente seus contextos académicos (turma + disciplina + semestre + turno)
- ✅ Importar notas de forma estruturada
- ✅ Publicar notas de forma controlada (não acidental)
- ✅ Delegar algumas tarefas ao delegado sem perder controlo
- ✅ Auditar quem fez o quê

**Pain Points:**
- ❌ Atualmente usa 3 sistemas diferentes (portal universidade + planilha + email)
- ❌ Medo de enviar notas acidentalmente
- ❌ Não sabe se delegado vai mexer em coisas críticas
- ❌ Sem histórico de quem fez upload quando

**Device:** Desktop (primário)

**Workflows Críticos:**
1. Login → Dashboard → Selecionar contexto académico ativo
2. Criar novo contexto (semestre/turma/disciplina/turno)
3. Upload CSV estudantes → Editar estudantes → Atribuir delegado
4. Upload CSV notas → Validar → Publicar (broadcast explícito)
5. Ver histórico de broadcasts/uploads

---

## Persona 2: Ana — Estudante Consultor

**Demographics:**
- Idade: 21 anos
- Tech level: Alto (mobile-native, redes sociais)
- Contexto: 3º ano, inscrita em 4 disciplinas este semestre

**Goals:**
- ✅ Ver notas logo após professor publicar
- ✅ Entender sua posição académica (notas atuais por disciplina)
- ✅ Saber calendário de provas/exames
- ✅ Consultar informações sem depender de WhatsApp

**Pain Points:**
- ❌ Espera dias para saber se passou numa disciplina
- ❌ Recebe nota por WhatsApp sem contexto (só um número)
- ❌ Não sabe se aquela é a nota final ou há mais avaliações
- ❌ Portal da universidade é lento e confuso no celular

**Device:** Mobile (80%), desktop (20%)

**Workflows Críticos:**
1. Login → Dashboard com notas publicadas por disciplina
2. Ver calendário (provas, exames, recursos)
3. Ver status académico (média, estado de cada disciplina)
4. Receber notificação quando notas forem publicadas

---

## Persona 3: João — Delegado de Turma

**Demographics:**
- Idade: 22 anos
- Tech level: Médio-alto
- Papel: Estudante que é delegado de sua turma
- Contexto: Mesma turma da Ana, mas com responsabilidades técnicas

**Goals:**
- ✅ Ajudar professor com uploads e organização
- ✅ Manter estudantes informados
- ✅ Ter acesso limitado (não quer mexer em tudo)
- ✅ Receber confirmação do professor antes de ações sensíveis

**Pain Points:**
- ❌ Medo de mexer em algo crítico
- ❌ Não sabe exatamente o que pode/não pode fazer
- ❌ Sem feedback claro do que mudou

**Device:** Desktop (primário), mobile (secundário)

**Workflows Críticos:**
1. Login como estudante (mas com permissões adicionais)
2. Ver painel restrito à sua turma
3. Ajudar em upload de estudantes (mas não pode apagar)
4. Preparar broadcast (mas precisa confirmação do professor)
5. Ver auditoria de sua turma

---

## Persona 4: Mariana — Coordenadora Pedagógica (Futuro)

**Demographics:**
- Papel: Supervisora de vários professores
- Tech level: Médio
- Contexto: Monitora qualidade de operações

**Goals (Future):**
- ✅ Ver resumo de uploads/broadcasts em todas as turmas
- ✅ Detectar inconsistências
- ✅ Gerar relatórios

**Status:** Fora de escopo para MVP, mas mencionada no PRD

---

## Matriz de Permissões (Baseada em FR15)

| Ação | Professor | Delegado | Estudante |
|------|-----------|----------|-----------|
| Login | ✅ | ✅ (como estud + perm) | ✅ |
| Ver contexto académico | ✅ | ✅ (turma própria) | ❌ |
| Criar contexto | ✅ | ❌ |❌ |
| Upload estudantes | ✅ | ⚠️ (precisa confirmação) | ❌ |
| Editar notas | ✅ | ❌ | ❌ |
| Publicar notas | ✅ | ❌ | ❌ |
| Ver notas publicadas | ✅ | ✅ | ✅ (suas próprias) |
| Atribuir delegado | ✅ | ❌ | ❌ |
| Ver auditoria | ✅ | ✅ (turma) | ❌ |

---

**Fonte:** PRD FR1-FR16, especialmente FR14-FR15 (delegado)  
**Status:** ✅ Baseadas em requisitos reais
