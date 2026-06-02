# Análise Introdutória do Projecto e Contexto

## Visão Geral do Projecto Existente

### Fonte de Análise
- Alinhamento direccionado de PRD em ambiente IDE.
- Fontes usadas: `docs/prd/index.md`, `docs/architecture/index.md`, `docs/architecture/system-architecture.md`, `docs/frontend/frontend-spec.md`, `docs/reviews/*.md`, `docs/qa/**/*.yml`, `docs/qa/**/*.md`, `docs/stories/epics/*.md` e `docs/stories/5.*.md`.
- O analista já classificou a mudança como `major_enhancement`; por isso, este documento consolida e alinha o PRD sem executar novo `document-project`.

### Estado Actual do Projecto
O projecto actual é um MVP local em Node.js/Express com frontend estático. O fluxo operacional existente permite upload de estudantes, upload de notas, geração de correspondência entre estudantes e notas, e envio em massa por WhatsApp através da Evolution API.

A persistência operacional actual usa ficheiros JSON locais. A arquitectura alvo documentada prevê evolução para uma plataforma académica com backend relevante em Python, base de dados relacional local, modelo académico explícito, publicação controlada por broadcast e portal do estudante.

## Análise da Documentação Disponível

### Documentação Disponível
- [x] Documentação de stack técnico: presente de forma parcial em `docs/architecture/system-architecture.md`.
- [x] Source tree/arquitectura: presente em `docs/architecture/index.md` e `docs/architecture/system-architecture.md`.
- [x] Normas de código: existe handoff mínimo em `docs/framework/coding-standards.md`; `docs/architecture.md` permanece fonte decisória principal até implementação.
- [x] Documentação de API: existe placeholder controlado em `docs/api/README.md`; OpenAPI será exportado quando o backend FastAPI existir.
- [ ] Documentação de API externa: integração Evolution API documentada por uso e variáveis, mas sem contrato formal.
- [x] Directrizes UX/UI: presente em `docs/frontend/frontend-spec.md`.
- [x] Documentação de dívida técnica: presente em `docs/prd/technical-debt-assessment.md`, `docs/prd/technical-debt-DRAFT.md`, `docs/reports/TECHNICAL-DEBT-REPORT.md` e reviews.
- [x] Outros: epics e stories em `docs/stories/`.

## Definição do Escopo da Melhoria

### Tipo de Melhoria
- [x] Adição de nova funcionalidade
- [x] Modificação maior de funcionalidade
- [x] Integração com novos sistemas
- [x] Actualização de stack tecnológico
- [x] Correcção de estabilidade e bugs
- [x] Revisão UI/UX
- [ ] Melhorias de performance/escalabilidade
- [ ] Outro

### Descrição da Melhoria
Transformar o MVP de upload, match e envio WhatsApp numa plataforma académica para gestão, cálculo, publicação e consulta de notas. A evolução deve introduzir domínio académico explícito, autenticação, papéis diferenciados, persistência relacional, publicação controlada e portal do estudante, preservando o fluxo crítico existente durante a transição.

### Avaliação de Impacto
- [ ] Impacto mínimo
- [ ] Impacto moderado
- [x] Impacto significativo
- [x] Impacto maior

## Objectivos e Contexto de Fundo

### Objectivos
- Permitir gestão de semestres, turnos, turmas, disciplinas, professores e estudantes.
- Substituir ficheiros JSON como fonte de verdade por uma base de dados real.
- Usar Python como parte central e relevante da solução.
- Separar notas internas de notas publicadas aos estudantes.
- Publicar notas e calendário apenas após acção explícita de broadcast.
- Disponibilizar portal do estudante com autenticação por número de estudante e palavra-passe.
- Modelar professor, delegado e estudante com limites claros de permissão.
- Manter o fluxo crítico actual verificável durante a transição.

### Contexto de Fundo
O fluxo actual resolve um problema operacional imediato: importar notas e enviar mensagens por WhatsApp. Porém, a evolução do produto exige consolidação académica por estudante, vários contextos de ensino, cálculo configurável, permissões, consulta autónoma pelo estudante e rastreabilidade das publicações.

Sem esta fundação, novas melhorias de frontend, testes ou comunicação continuarão dependentes de um modelo de dados insuficiente para o produto académico pretendido.

## Registo de Alterações

| Alteração | Data | Versão | Descrição | Autor |
|---|---:|---:|---|---|
| PRD formal brownfield criado | 2026-05-27 | 1.0 | Consolidação monolítica do PRD a partir dos artefactos existentes, com decisões em aberto explicitadas | Morgan, PM |
