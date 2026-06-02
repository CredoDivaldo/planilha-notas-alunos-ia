# Objectivos de Melhoria da Interface

## Integração com a UI Existente
A UI actual é uma página única operacional com cinco etapas. A evolução deve manter clareza de sequência e baixo atrito para docentes, introduzindo gradualmente estados `locked`, `active`, `completed` e `error`, feedback semântico e confirmação acessível para envio real.

## Ecrãs e Vistas Novos ou Alterados
- Painel operacional do professor.
- Vista técnica reduzida do delegado.
- Portal do estudante.
- Gestão de contextos académicos.
- Gestão de notas e componentes de avaliação.
- Calendário de provas, exames e recursos.
- Fluxo de publicação/broadcast.

## Requisitos de Consistência UI
- Usar os princípios de `docs/frontend/frontend-spec.md` para StepCards, StatusMessage, Button e MatchDataView.
- Garantir labels, `aria-live`, foco visível, navegação por teclado e contraste AA.
- Bloquear acções críticas quando pré-condições não estiverem cumpridas.
- Preservar contexto válido anterior quando uma nova operação falhar.
