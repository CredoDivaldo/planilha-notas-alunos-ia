// UpcomingEventsList — events in next 30 days, grouped by date (AC9)
// T9

import type { CalendarEvent } from '@/components/molecules/EventDot'
import { eventColorTextClass } from '@/components/molecules/EventDot'

interface UpcomingEventsListProps {
  events: CalendarEvent[]
}

const TYPE_LABEL: Record<string, string> = {
  exame:    '🔵 Exame',
  recurso:  '🟠 Recurso',
  entrega:  '🟣 Entrega',
  reuniao:  '🟢 Reunião',
  feriado:  '🔴 Feriado',
  outro:    '⚪ Outro',
}

function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('pt-PT', { weekday: 'short', day: '2-digit', month: 'short' })
}

export function UpcomingEventsList({ events }: UpcomingEventsListProps) {
  // Filter: next 30 days from today
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const limit = new Date(today)
  limit.setDate(limit.getDate() + 30)

  const upcoming = events.filter((ev) => {
    const d = new Date(ev.date + 'T00:00:00')
    return d >= today && d <= limit
  }).sort((a, b) => a.date.localeCompare(b.date))

  // Group by date
  const grouped = new Map<string, CalendarEvent[]>()
  for (const ev of upcoming) {
    if (!grouped.has(ev.date)) grouped.set(ev.date, [])
    grouped.get(ev.date)!.push(ev)
  }

  if (upcoming.length === 0) {
    return (
      <div className="bg-card rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold text-foreground mb-2">Próximos Eventos</h3>
        <p className="text-sm text-muted-foreground">Sem eventos nos próximos 30 dias.</p>
      </div>
    )
  }

  return (
    <div className="bg-card rounded-lg border border-border p-4">
      <h3 className="text-sm font-semibold text-foreground mb-3">Próximos Eventos</h3>
      <div className="flex flex-col gap-3">
        {Array.from(grouped.entries()).map(([date, dayEvents]) => (
          <div key={date}>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium text-muted-foreground"><span className="flex items-center gap-1"><Calendar className="size-3" /> {formatDate(date)}</span></span>
            </div>
            <div className="flex flex-col gap-1 pl-4">
              {dayEvents.map((ev) => (
                <div
                  key={ev.id}
                  className={[
                    'rounded-md border px-3 py-2 text-xs',
                    eventColorTextClass(ev.type),
                  ].join(' ')}
                >
                  <div className="font-medium">
                    {TYPE_LABEL[ev.type] ?? '⚪'} {ev.title}
                  </div>
                  <div className="flex flex-wrap gap-2 mt-0.5 opacity-75">
                    {ev.time && <span>🕐 {ev.time}</span>}
                    {ev.location && <span>📍 {ev.location}</span>}
                    {ev.description && <span>{ev.description}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
