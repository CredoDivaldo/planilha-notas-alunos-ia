# Epic 4: UX Refinement

**Epic ID:** EPIC-4
**Status:** Draft
**Created:** 2026-05-02
**Owner:** @pm (Morgan)

---

## Overview

Implementar UX foundations: accessibility (WCAG AA), responsive design, design system, confirmation dialogs, e polling para estado de conexão WhatsApp.

## Business Context

O MVP atual possui **UX Score 4/10** (Nielsen heuristics):
- Sem accessibility → Excludes users with disabilities
- Sem responsive → Poor mobile experience
- Sem design system → Maintenance burden
- Sem confirmation dialogs → Accidental sends risk
- Sem polling → Manual state checking

UX Specialist verdict: **APPROVED WITH CONCERNS**

## Scope

### IN
- UX-003: Accessibility basics (ARIA, focus, labels)
- UX-004: Form validation feedback
- UX-005: QR code polling
- UX-006: Design system tokens
- UX-007: Responsive design breakpoints
- UX-008: Confirmation dialogs for send action
- State gating for workflow steps

### OUT
- Full component library
- Advanced animations
- Dashboard/analytics UI
- Multi-language support

## Success Criteria

| Criteria | Metric |
|----------|--------|
| Accessibility | WCAG 2.2 AA compliance basics |
| Focus management | Tab order logical, focus visible |
| Responsive | Mobile (320px), Tablet (768px), Desktop (1024px) |
| Design tokens | CSS variables for colors, spacing, typography |
| Confirmation | Modal before send (replaces alert) |
| Polling | Auto-update connection state (5s interval) |
| UX Gate | APPROVED (no concerns) |

## Dependencies

- **EPIC-2:** Quality foundation (testing UX changes)
- **EPIC-3:** Security (auth for confirmation)

## Stories

### Story 4.1: Accessibility Basics (UX-003)
- **Points:** 4
- **Owner:** @ux-design-expert
- **Priority:** P1
- **Description:** Add ARIA labels, focus indicators, semantic structure
- **File:** `docs/stories/4.1.accessibility-basics.md`

### Story 4.2: Form Validation Feedback (UX-004)
- **Points:** 2
- **Owner:** @ux-design-expert
- **Priority:** P1
- **Description:** Client-side validation before upload
- **File:** `docs/stories/4.2.form-validation-feedback.md`

### Story 4.3: QR Polling (UX-005)
- **Points:** 2
- **Owner:** @dev
- **Priority:** P1
- **Description:** Implement polling for Evolution connection state
- **File:** `docs/stories/4.3.qr-polling.md`

### Story 4.4: Design System Tokens (UX-006)
- **Points:** 2
- **Owner:** @ux-design-expert
- **Priority:** P2
- **Description:** Define CSS variables for colors, spacing, typography
- **File:** `docs/stories/4.4.design-system-tokens.md`

### Story 4.5: Responsive Design (UX-007)
- **Points:** 2
- **Owner:** @ux-design-expert
- **Priority:** P2
- **Description:** Add media queries, responsive grid, mobile cards
- **File:** `docs/stories/4.5.responsive-design.md`

### Story 4.6: Confirmation Dialogs (UX-008)
- **Points:** 1
- **Owner:** @ux-design-expert
- **Priority:** P2
- **Description:** Replace alert() with accessible confirmation modal
- **File:** `docs/stories/4.6.confirmation-dialogs.md`

### Story 4.7: State Gating
- **Points:** 3
- **Owner:** @ux-design-expert + @dev
- **Priority:** P1
- **Description:** Lock/unlock steps based on prerequisites
- **File:** `docs/stories/4.7.state-gating.md`

## Timeline

- **Sprint 2:** Week 2 (Stories 4.1-4.3, 4.7)
- **Sprint 3:** Week 3-4 (Stories 4.4-4.6)
- **Effort Total:** 14 points (~14h)

## Risks

| Risk | Mitigation |
|------|------------|
| Accessibility testing complexity | Use axe-core automated + manual checklist |
| Responsive breaks desktop | Test all breakpoints |
| Modal accessibility issues | Follow WCAG modal pattern |

---

*Epic created by @pm (Morgan) — 2026-05-02*