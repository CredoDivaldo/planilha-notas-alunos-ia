// MonthCalendar — monthly grid with EventDots, month navigation, tooltip on event click
// T5 — reusable component (Story 7.6, Story 7.8)
// Story 7.8 — adapted: added allowEdit and onEventClick props (backward-compatible)

import { Calendar } from 'lucide-react'
import { useState } from 'react'
import { EventDot } from '@/components/molecules/EventDot'
import type { CalendarEvent } from '@/components/molecules/EventDot'
import { eventColorTextClass } from '@/components/molecules/EventDot'

interface MonthCalendarProps {
  events: CalendarEvent[]
  /** Enable click-to-select events for edit/detail panel. default: false */
  allowEdit?: boolean
  /** Callback when an event dot is clicked (requires allowEdit=true or will also fire for read-only) */
  onEventClick?: (event: CalendarEvent) => void
  /** Currently selected event id, controlled from parent when allowEdit=true */
  selectedEventId?: string | null
}

const WEEKDAY_LABELS = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D']
const MONTH_NAMES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
]

function isoDate(year: number, month: number, day: number): string {
  return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function getDaysInMonth(year: number, month: number): number {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstWeekday(year: number, month: number): number {
  // 0=Sun, shift so week starts on Monday (0=Mon … 6=Sun)
  const d = new Date(year, month, 1).getDay()
  return (d + 6) % 7
}

export function MonthCalendar({
  events,
  allowEdit = false,
  onEventClick,
  selectedEventId,
}: MonthCalendarProps) {
  const today = new Date()
  const [year, setYear] = useState(today.getFullYear())
  const [month, setMonth] = useState(today.getMonth())
  // Internal active event used only when no external onEventClick provided (Story 7.6 compat)
  const [internalActiveEvent, setInternalActiveEvent] = useState<CalendarEvent | null>(null)

  const activeEvent = onEventClick ? null : internalActiveEvent

  const prevMonth = () => {
    if (month === 0) { setYear(y => y - 1); setMonth(11) }
    else setMonth(m => m - 1)
    setInternalActiveEvent(null)
  }
  const nextMonth = () => {
    if (month === 11) { setYear(y => y + 1); setMonth(0) }
    else setMonth(m => m + 1)
    setInternalActiveEvent(null)
  }

  const daysInMonth = getDaysInMonth(year, month)
  const firstWeekday = getFirstWeekday(year, month)

  // Map events to dates for this month
  const eventsByDate = new Map<string, CalendarEvent[]>()
  for (const ev of events) {
    if (!eventsByDate.has(ev.date)) eventsByDate.set(ev.date, [])
    eventsByDate.get(ev.date)!.push(ev)
  }

  // Build grid cells: leading empty + day cells
  const cells: (null | number)[] = [
    ...Array(firstWeekday).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ]

  const todayStr = isoDate(today.getFullYear(), today.getMonth(), today.getDate())

  return (
    <div className="bg-card rounded-lg border border-border p-4 select-none">
      {/* Month nav */}
      <div className="flex items-center justify-between mb-3">
        <button
          type="button"
          onClick={prevMonth}
          aria-label="Mês anterior"
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-slate-100 text-muted-foreground hover:text-slate-800 transition-colors text-sm"
        >
          ‹
        </button>
        <span className="text-sm font-semibold text-slate-800">
          {MONTH_NAMES[month]} {year}
        </span>
        <button
          type="button"
          onClick={nextMonth}
          aria-label="Próximo mês"
          className="w-7 h-7 flex items-center justify-center rounded hover:bg-slate-100 text-muted-foreground hover:text-slate-800 transition-colors text-sm"
        >
          ›
        </button>
      </div>

      {/* Weekday headers */}
      <div className="grid grid-cols-7 mb-1">
        {WEEKDAY_LABELS.map((d, i) => (
          <div key={i} className="text-center text-[10px] font-medium text-muted-foreground py-1">
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7 gap-y-1">
        {cells.map((day, idx) => {
          if (day === null) return <div key={`empty-${idx}`} />
          const dateStr = isoDate(year, month, day)
          const dayEvents = eventsByDate.get(dateStr) ?? []
          const isToday = dateStr === todayStr

          return (
            <div
              key={dateStr}
              className="flex flex-col items-center gap-0.5"
            >
              <span
                className={[
                  'text-xs w-6 h-6 flex items-center justify-center rounded-full',
                  isToday
                    ? 'bg-[#0D6EFD] text-white font-bold'
                    : 'text-foreground',
                ].join(' ')}
              >
                {day}
              </span>
              {dayEvents.length > 0 && (
                <div className="flex flex-wrap justify-center gap-0.5">
                  {dayEvents.slice(0, 3).map((ev) => {
                    const isSelected = selectedEventId === ev.id
                    return (
                      <button
                        key={ev.id}
                        type="button"
                        title={[ev.title, ev.time, ev.location].filter(Boolean).join(' · ')}
                        aria-label={`${dateStr} - ${ev.title}`}
                        aria-pressed={isSelected}
                        onClick={() => {
                          if (onEventClick) {
                            onEventClick(ev)
                          } else {
                            setInternalActiveEvent(prev => prev?.id === ev.id ? null : ev)
                          }
                        }}
                        className={[
                          'focus:outline-none',
                          (allowEdit || onEventClick) ? 'cursor-pointer' : '',
                          isSelected ? 'ring-2 ring-offset-1 ring-current rounded-full' : '',
                        ].join(' ')}
                      >
                        <EventDot event={ev} showTooltip={false} />
                      </button>
                    )
                  })}
                  {dayEvents.length > 3 && (
                    <span className="text-[9px] text-muted-foreground">+{dayEvents.length - 3}</span>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Tooltip / event detail */}
      {activeEvent && (
        <div
          role="tooltip"
          className={[
            'mt-3 rounded-md border px-3 py-2 text-xs',
            eventColorTextClass(activeEvent.type),
          ].join(' ')}
        >
          <div className="font-semibold mb-0.5">{activeEvent.title}</div>
          <div className="flex flex-wrap gap-2 text-xs opacity-80">
            {activeEvent.date && <span><span className="flex items-center gap-1"><Calendar className="size-3" /> {activeEvent.date}</span></span>}
            {activeEvent.time && <span>🕐 {activeEvent.time}</span>}
            {activeEvent.location && <span>📍 {activeEvent.location}</span>}
            {activeEvent.description && <span>{activeEvent.description}</span>}
          </div>
        </div>
      )}
    </div>
  )
}
