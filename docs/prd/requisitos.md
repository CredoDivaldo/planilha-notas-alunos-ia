# Requisitos

## Funcionais

1. **FR1:** O sistema deve preservar o fluxo crítico existente de upload de estudantes, upload de notas, geração de match e envio WhatsApp até existir substituição validada.
2. **FR2:** O sistema deve permitir configurar e gerir semestres, turmas, turnos, disciplinas, cursos e relações entre estes elementos.
3. **FR3:** O sistema deve permitir ao professor configurar múltiplos contextos próprios no formato `turma + disciplina + semestre + turno`.
4. **FR4:** O sistema deve permitir cadastrar estudantes, actualizar contactos e associá-los aos contextos académicos relevantes através do número de estudante.
5. **FR5:** O sistema deve permitir importar notas por ficheiros estruturados para uma disciplina de uma turma num semestre específico.
6. **FR6:** O sistema deve permitir corrigir e completar manualmente notas e componentes de avaliação.
7. **FR7:** O sistema deve calcular resultados académicos com base numa fórmula institucional configurável; a fórmula oficial permanece pendente de validação.
8. **FR8:** O sistema deve distinguir dados internos lançados de dados publicados aos estudantes.
9. **FR9:** O sistema deve tornar notas visíveis no portal apenas após broadcast explícito.
10. **FR10:** O sistema deve permitir novo broadcast quando notas ou datas publicadas forem alteradas.
11. **FR11:** O sistema deve permitir broadcast por WhatsApp como canal principal e e-mail como canal complementar quando disponível.
12. **FR12:** O sistema deve permitir ao estudante consultar notas publicadas, estado académico actual, turma, curso e calendário de provas, exames e recursos.
13. **FR13:** O sistema deve suportar login do estudante por número de estudante e palavra-passe, com troca obrigatória no primeiro acesso.
14. **FR14:** O sistema deve permitir perfil de delegado com permissões técnicas limitadas à sua turma.
15. **FR15:** O sistema deve impedir que delegados modifiquem notas directamente, removam turmas ou executem acções sensíveis sem validação do professor.
16. **FR16:** O sistema deve registar uploads, alterações, broadcasts, aprovações e operações sensíveis para auditabilidade operacional.
17. **FR17:** O sistema deve receber mensagens WhatsApp de estudantes via webhook da Evolution API e identificar o aluno pelo número de telefone registado.
18. **FR18:** O sistema deve usar um modelo de linguagem (IA) para interpretar perguntas dos estudantes sobre as suas notas em linguagem natural, em Português.
19. **FR19:** O sistema deve responder ao estudante via WhatsApp com informação sobre as suas notas publicadas, respeitando FR8 e FR9 — apenas dados explicitamente publicados são expostos.
20. **FR20:** O chatbot deve recusar responder sobre notas ainda não publicadas e informar o estudante de forma clara e amigável.

## Não Funcionais

1. **NFR1:** A persistência académica alvo deve usar base de dados relacional como fonte de verdade, substituindo JSON como persistência primária.
2. **NFR2:** Python deve ser usado de forma central na solução, preferencialmente no backend principal; uma alternativa aceitável é motor académico/importação/cálculo em Python durante uma transição controlada.
3. **NFR3:** O sistema deve proteger acesso a notas e operações administrativas por autenticação e autorização adequadas aos papéis.
4. **NFR4:** O modelo deve suportar evolução futura de fórmulas, componentes de avaliação e regras institucionais sem reescrita estrutural.
5. **NFR5:** O sistema deve manter qualidade verificável por `npm run lint`, `npm run typecheck`, `npm test` e comandos equivalentes que forem introduzidos para Python.
6. **NFR6:** As interfaces novas ou alteradas devem seguir os requisitos de acessibilidade WCAG 2.2 AA definidos no frontend spec.
7. **NFR7:** Operações críticas devem ter feedback claro, estados de erro consistentes e prevenção de acções fora de sequência.
8. **NFR8:** O portal do estudante deve exibir apenas a versão publicada actual, sem expor histórico detalhado de alterações.

## Requisitos de Compatibilidade

1. **CR1:** As capacidades actuais de importação CSV, match e envio WhatsApp não devem ser quebradas sem substituição funcional e validação explícita.
2. **CR2:** Ficheiros JSON existentes podem ser usados como legado, artefacto transitório ou fonte de migração, mas não devem permanecer como fonte de verdade académica alvo.
3. **CR3:** A experiência operacional do professor deve manter a sequência conceptual upload -> match -> envio/publicação durante a transição.
4. **CR4:** A integração com Evolution API deve continuar suportada enquanto o WhatsApp for o canal principal de broadcast.
5. **CR5:** A publicação para portal e notificações deve permanecer dependente de acção humana explícita, sem automação silenciosa.
