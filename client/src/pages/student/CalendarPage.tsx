// CalendarPage — student read-only view
// Story 7.8 — T1 (student variant)

import { Download } from 'lucide-react'
import { useState, useEffect } from 'react'
import { AppHeader } from '@/components/organisms/AppHeader'
import { MonthCalendar } from '@/components/organisms/MonthCalendar'
import { UpcomingEventsList } from '@/components/organisms/UpcomingEventsList'
import { EventDetailPanel } from '@/components/organisms/EventDetailPanel'
import { apiFetch } from '@/lib/api'
import type { CalendarEvent } from '@/components/molecules/EventDot'

// ---------------------------------------------------------------------------
// Mock data — events with visivel_estudantes=true
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// ICS export (read-only for student — AC12)
// ---------------------------------------------------------------------------
function generateIcs(events: CalendarEvent[]): string {
  const lines: string[] = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Planilha Notas//PT']
  for (const ev of events) {
    const base = ev.date.replace(/-/g, '')
    const t = ev.time ? ev.time.split('–')[0].replace(':', '') + '00' : undefined
    lines.push('BEGIN:VEVENT')
    lines.push(`UID:${ev.id}@planilha-notas`)
    lines.push(`DTSTART:${t ? `${base}T${t}` : base}`)
    lines.push(`SUMMARY:${ev.title}`)
    if (ev.location) lines.push(`LOCATION:${ev.location}`)
    lines.push('END:VEVENT')
  }
  lines.push('END:VCALENDAR')
  return lines.join('\r\n')
}

function downloadIcs(events: CalendarEvent[]) {
  const blob = new Blob([generateIcs(events)], { type: 'text/calendar' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'calendario.ics'
  a.click()
  URL.revokeObjectURL(url)
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function StudentCalendarPage() {
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null)

  // Load the student's published calendar events from the portal endpoint.
  // The backend returns { events: [{id, date, time, type, title, location}] }.
  useEffect(() => {
    apiFetch<{ events: CalendarEvent[] }>('/api/v1/portal/me/calendar')
      .then((d) => setEvents(d.events ?? []))
      .catch(() => setEvents([]))
  }, [])

  // 7-day filter for upcoming section
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const limit7 = new Date(today)
  limit7.setDate(limit7.getDate() + 7)
  const next7Events = events.filter((ev) => {
    const d = new Date(ev.date + 'T00:00:00')
    return d >= today && d <= limit7
  })

  return (
    <div className="min-h-screen bg-muted/50">
      <AppHeader activeTab="calendario" />

      <main className="max-w-[1280px] mx-auto px-6 py-6 flex flex-col gap-5">

        {/* Title + toolbar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-xl font-bold text-foreground">Calendário Académico</h1>
          <button
            type="button"
            onClick={() => downloadIcs(events)}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted/50 transition-colors"
          >
            <><Download className="size-4" /> Descarregar .ics</>
          </button>
        </div>

        {/* 2-col layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-5">
          <div className="flex flex-col gap-5">
            {/* AC13 — MonthCalendar with onEventClick for read-only detail */}
            <MonthCalendar
              events={events}
              onEventClick={(ev) => setSelectedEvent((prev) => prev?.id === ev.id ? null : ev)}
              selectedEventId={selectedEvent?.id ?? null}
            />

            {/* AC7 — Próximos 7 dias */}
            <div>
              <h2 className="text-sm font-semibold text-foreground mb-2">
                Próximos Eventos (7 dias)
              </h2>
              <UpcomingEventsList events={next7Events} />
            </div>
          </div>

          {/* Right sidebar: read-only detail — no edit/delete buttons — AC6, AC14 */}
          <EventDetailPanel
            event={selectedEvent}
            role="estudante"
            onClose={() => setSelectedEvent(null)}
          />
        </div>
      </main>
    </div>
  )
}
