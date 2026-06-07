/**
 * Unit tests for MonthCalendar logic — Story 7.6 (T14)
 * Tests grid calculation helpers, month navigation state, and event filtering.
 *
 * Uses inline re-implementation of core logic from MonthCalendar.tsx.
 */

'use strict'

// ---------------------------------------------------------------------------
// Re-implementation of core calendar logic from MonthCalendar.tsx
// ---------------------------------------------------------------------------

function getDaysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstWeekday(year, month) {
  // Week starts Monday: 0=Mon, 6=Sun
  const d = new Date(year, month, 1).getDay()
  return (d + 6) % 7
}

function isoDate(year, month, day) {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function buildCalendarGrid(year, month) {
  const daysInMonth = getDaysInMonth(year, month)
  const firstWeekday = getFirstWeekday(year, month)
  return [
    ...Array(firstWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]
}

function filterEventsForMonth(events, year, month) {
  const prefix = `${year}-${String(month + 1).padStart(2, '0')}-`
  return events.filter((e) => e.date.startsWith(prefix))
}

function prevMonth(year, month) {
  if (month === 0) return { year: year - 1, month: 11 }
  return { year, month: month - 1 }
}

function nextMonth(year, month) {
  if (month === 11) return { year: year + 1, month: 0 }
  return { year, month: month + 1 }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('getDaysInMonth', () => {
  test('June 2026 has 30 days', () => {
    expect(getDaysInMonth(2026, 5)).toBe(30) // month 5 = June
  })

  test('January 2026 has 31 days', () => {
    expect(getDaysInMonth(2026, 0)).toBe(31)
  })

  test('February 2024 has 29 days (leap year)', () => {
    expect(getDaysInMonth(2024, 1)).toBe(29)
  })

  test('February 2025 has 28 days (non-leap)', () => {
    expect(getDaysInMonth(2025, 1)).toBe(28)
  })
})

describe('getFirstWeekday (week starts Monday)', () => {
  test('June 2026 starts on Monday (0)', () => {
    // 1 June 2026 is a Monday → index 0
    expect(getFirstWeekday(2026, 5)).toBe(0)
  })

  test('January 2026 starts on Thursday (3)', () => {
    // 1 January 2026 is a Thursday → index 3
    expect(getFirstWeekday(2026, 0)).toBe(3)
  })
})

describe('buildCalendarGrid', () => {
  test('grid for June 2026: 0 leading nulls + 30 days', () => {
    const grid = buildCalendarGrid(2026, 5)
    expect(grid.length).toBe(30) // no leading nulls (June starts Monday)
    expect(grid[0]).toBe(1)
    expect(grid[29]).toBe(30)
  })

  test('grid for January 2026: 3 leading nulls (Thu=index 3) + 31 days', () => {
    const grid = buildCalendarGrid(2026, 0)
    expect(grid[0]).toBeNull()
    expect(grid[1]).toBeNull()
    expect(grid[2]).toBeNull()
    expect(grid[3]).toBe(1) // first day in Jan
    expect(grid.length).toBe(34) // 3 + 31
  })

  test('isoDate helper formats correctly', () => {
    expect(isoDate(2026, 5, 17)).toBe('2026-06-17')
    expect(isoDate(2026, 0, 1)).toBe('2026-01-01')
  })
})

describe('filterEventsForMonth', () => {
  const events = [
    { id: '1', date: '2026-06-10', type: 'exame', title: 'Exame Inglês' },
    { id: '2', date: '2026-06-24', type: 'recurso', title: 'Recurso' },
    { id: '3', date: '2026-07-05', type: 'exame', title: 'Exame Julho' },
    { id: '4', date: '2026-05-31', type: 'outro', title: 'Evento Maio' },
  ]

  test('returns only June 2026 events', () => {
    const result = filterEventsForMonth(events, 2026, 5)
    expect(result).toHaveLength(2)
    expect(result.map((e) => e.id)).toEqual(['1', '2'])
  })

  test('returns empty array when no events in month', () => {
    const result = filterEventsForMonth(events, 2026, 8) // September
    expect(result).toHaveLength(0)
  })
})

describe('month navigation', () => {
  test('prevMonth from Jan 2026 → Dec 2025', () => {
    expect(prevMonth(2026, 0)).toEqual({ year: 2025, month: 11 })
  })

  test('prevMonth from June 2026 → May 2026', () => {
    expect(prevMonth(2026, 5)).toEqual({ year: 2026, month: 4 })
  })

  test('nextMonth from Dec 2026 → Jan 2027', () => {
    expect(nextMonth(2026, 11)).toEqual({ year: 2027, month: 0 })
  })

  test('nextMonth from June 2026 → July 2026', () => {
    expect(nextMonth(2026, 5)).toEqual({ year: 2026, month: 6 })
  })
})
