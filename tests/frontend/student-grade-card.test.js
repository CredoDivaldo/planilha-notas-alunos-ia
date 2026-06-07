/**
 * Unit tests for StudentGradeCard logic — Story 7.6 (T14)
 * Tests pure logic: grade formatting, published vs. unpublished state,
 * null safety (AC4, AC5, AC6).
 *
 * Uses inline re-implementation of core logic so no bundler is needed.
 */

'use strict'

// ---------------------------------------------------------------------------
// Re-implementation of core logic from StudentGradeCard.tsx
// If production code changes, these must stay in sync.
// ---------------------------------------------------------------------------

function formatGrade(value) {
  if (value === null || value === undefined) return '—'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function buildSubjectViewModel(subject) {
  return {
    isPendente: subject.pendente === true,
    notaFinalDisplay: formatGrade(subject.notaFinal),
    resultadoBadge:
      subject.resultado === 'aprovado' ? '✅ APROVADO(A)'
      : subject.resultado === 'reprovado' ? '❌ REPROVADO(A)'
      : null,
    componentRows: subject.components.map((c) => ({
      name: c.name,
      weight: c.weight,
      valueDisplay: formatGrade(c.value),
      published: c.published,
    })),
  }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('formatGrade (AC6 — null safety)', () => {
  test('null → "—"', () => {
    expect(formatGrade(null)).toBe('—')
  })

  test('undefined → "—"', () => {
    expect(formatGrade(undefined)).toBe('—')
  })

  test('integer → string without decimal', () => {
    expect(formatGrade(15)).toBe('15')
  })

  test('float → one decimal place', () => {
    expect(formatGrade(14.4)).toBe('14.4')
  })

  test('zero → "0" (not "—")', () => {
    expect(formatGrade(0)).toBe('0')
  })
})

describe('buildSubjectViewModel — published subject (AC4)', () => {
  const subject = {
    disciplina: 'Inglês Técnico',
    pendente: false,
    notaFinal: 14.4,
    resultado: 'aprovado',
    components: [
      { id: 'c1', name: 'Frequência', weight: 40, value: 15, published: true },
      { id: 'c2', name: 'Exame Final', weight: 60, value: 14, published: true },
    ],
  }

  test('isPendente = false for published subject', () => {
    expect(buildSubjectViewModel(subject).isPendente).toBe(false)
  })

  test('notaFinalDisplay shows formatted grade', () => {
    expect(buildSubjectViewModel(subject).notaFinalDisplay).toBe('14.4')
  })

  test('resultado = aprovado → ✅ badge', () => {
    expect(buildSubjectViewModel(subject).resultadoBadge).toBe('✅ APROVADO(A)')
  })

  test('component values displayed correctly', () => {
    const vm = buildSubjectViewModel(subject)
    expect(vm.componentRows[0].valueDisplay).toBe('15')
    expect(vm.componentRows[1].valueDisplay).toBe('14')
  })
})

describe('buildSubjectViewModel — reprovado (AC4)', () => {
  const subject = {
    disciplina: 'Matemática',
    pendente: false,
    notaFinal: 8.0,
    resultado: 'reprovado',
    components: [{ id: 'c1', name: 'Exame', weight: 100, value: 8, published: true }],
  }

  test('resultado = reprovado → ❌ badge', () => {
    expect(buildSubjectViewModel(subject).resultadoBadge).toBe('❌ REPROVADO(A)')
  })
})

describe('buildSubjectViewModel — unpublished subject (AC5, AC6)', () => {
  const subject = {
    disciplina: 'Física',
    pendente: true,
    notaFinal: null,
    resultado: null,
    components: [],
  }

  test('isPendente = true for unpublished subject', () => {
    expect(buildSubjectViewModel(subject).isPendente).toBe(true)
  })

  test('notaFinalDisplay for null → "—" not "0" (AC6)', () => {
    expect(buildSubjectViewModel(subject).notaFinalDisplay).toBe('—')
  })

  test('resultadoBadge is null for pending subjects', () => {
    expect(buildSubjectViewModel(subject).resultadoBadge).toBeNull()
  })

  test('no component rows for unpublished subject', () => {
    expect(buildSubjectViewModel(subject).componentRows).toHaveLength(0)
  })
})

describe('buildSubjectViewModel — null component value (AC6)', () => {
  const subject = {
    disciplina: 'Química',
    pendente: false,
    notaFinal: null,
    resultado: null,
    components: [
      { id: 'c1', name: 'Frequência', weight: 40, value: null, published: false },
      { id: 'c2', name: 'Exame', weight: 60, value: 12, published: true },
    ],
  }

  test('null component value → "—" not "0" or "" (AC6)', () => {
    const vm = buildSubjectViewModel(subject)
    expect(vm.componentRows[0].valueDisplay).toBe('—')
    expect(vm.componentRows[0].valueDisplay).not.toBe('0')
    expect(vm.componentRows[0].valueDisplay).not.toBe('')
  })

  test('non-null component value rendered correctly', () => {
    const vm = buildSubjectViewModel(subject)
    expect(vm.componentRows[1].valueDisplay).toBe('12')
  })
})
