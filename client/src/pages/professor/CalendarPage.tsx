// CalendarPage — professor view with full CRUD, context selector, month/list view, .ics export
// Story 7.8 — T1, T3, T4, T8, T9, T10, T11, T13

import { Calendar } from 'lucide-react'
import { useState, useCallback, useEffect } from 'react'
import { AppHeader } from '@/components/organisms/AppHeader'
import { MonthCalendar } from '@/components/organisms/MonthCalendar'
import { UpcomingEventsList } from '@/components/organisms/UpcomingEventsList'
import { EventDetailPanel } from '@/components/organisms/EventDetailPanel'
import { EventModal } from '@/components/organisms/EventModal'
import type { EventFormData, ContextOption } from '@/components/organisms/EventModal'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { apiFetch } from '@/lib/api'
import type { CalendarEvent } from '@/components/molecules/EventDot'
import { useActiveContext } from '@/contexts/ActiveContextContext'

// ---------------------------------------------------------------------------
// Fallback data (used when backend is unreachable in dev; not test fixtures)
// ---------------------------------------------------------------------------
// Extended CalendarEvent with optional context_id for filtering
type CalendarEventWithContext = CalendarEvent & { context_id?: string }

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// T11 — ICS export (manual Blob, no npm package)
function generateIcs(events: CalendarEvent[]): string {
  function icsDate(dateStr: string, timeStr?: string): string {
    const base = dateStr.replace(/-/g, '')
    if (!timeStr) return base
    const t = timeStr.split('–')[0].replace(':', '') + '00'
    return `${base}T${t}`
  }

  const lines: string[] = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Planilha Notas//PT']
  for (const ev of events) {
    lines.push('BEGIN:VEVENT')
    lines.push(`UID:${ev.id}@planilha-notas`)
    lines.push(`DTSTART:${icsDate(ev.date, ev.time)}`)
    if (ev.time?.includes('–')) {
      const end = ev.time.split('–')[1]
      lines.push(`DTEND:${icsDate(ev.date, end)}`)
    }
    lines.push(`SUMMARY:${ev.title}`)
    if (ev.location) lines.push(`LOCATION:${ev.location}`)
    if (ev.description) lines.push(`DESCRIPTION:${ev.description}`)
    lines.push('END:VEVENT')
  }
  lines.push('END:VCALENDAR')
  return lines.join('\r\n')
}

function downloadIcs(events: CalendarEvent[]) {
  const ics = generateIcs(events)
  const blob = new Blob([ics], { type: 'text/calendar' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'calendario.ics'
  a.click()
  URL.revokeObjectURL(url)
}

// ---------------------------------------------------------------------------
// View mode type
// ---------------------------------------------------------------------------
type ViewMode = 'mes' | 'lista'

// ---------------------------------------------------------------------------
// List view
// ---------------------------------------------------------------------------
function ListViewPanel({ events }: { events: CalendarEvent[] }) {
  const sorted = [...events].sort((a, b) => a.date.localeCompare(b.date))

  if (sorted.length === 0) {
    return (
      <div className="bg-card rounded-lg border border-border p-8 text-center text-muted-foreground text-sm">
        Sem eventos neste período.
      </div>
    )
  }

  // Group by month-year
  const grouped = new Map<string, CalendarEvent[]>()
  for (const ev of sorted) {
    const key = ev.date.slice(0, 7)
    if (!grouped.has(key)) grouped.set(key, [])
    grouped.get(key)!.push(ev)
  }

  const MONTH_NAMES = [
    'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
  ]

  function monthLabel(key: string): string {
    const [y, m] = key.split('-')
    return `${MONTH_NAMES[parseInt(m, 10) - 1]} ${y}`
  }

  const EVENT_COLOR_BG: Record<string, string> = {
    exame:   'bg-blue-50 border-blue-200 text-blue-800',
    outro:   'bg-purple-50 border-purple-200 text-purple-800',
    recurso: 'bg-orange-50 border-orange-200 text-orange-800',
    entrega: 'bg-success/10 border-success/20 text-success',
    feriado: 'bg-destructive/10 border-destructive/20 text-destructive',
    reuniao: 'bg-success/10 border-success/20 text-success',
  }

  return (
    <div className="flex flex-col gap-6">
      {Array.from(grouped.entries()).map(([key, evs]) => (
        <div key={key}>
          <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">
            {monthLabel(key)}
          </h3>
          <div className="flex flex-col gap-2">
            {evs.map((ev) => (
              <div
                key={ev.id}
                className={[
                  'rounded-lg border px-4 py-3 text-sm',
                  EVENT_COLOR_BG[ev.type] ?? 'bg-muted/50 border-border text-foreground',
                ].join(' ')}
              >
                <div className="font-medium">{ev.title}</div>
                <div className="flex flex-wrap gap-3 mt-1 text-xs opacity-75">
                  <span className="flex items-center gap-1"><Calendar className="size-3" /> {ev.date}</span>
                  {ev.time && <span>🕐 {ev.time}</span>}
                  {ev.location && <span>📍 {ev.location}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Professor CalendarPage
// ---------------------------------------------------------------------------
export default function CalendarPage() {
  const { contexts } = useActiveContext()

  // Map real contexts to ContextOption format for EventModal
  const contextOptions: ContextOption[] = contexts.map((c) => ({
    id: c.id,
    label: `${c.turma} · ${c.disciplina} · ${c.semestre}`,
  }))

  // Data
  const [events, setEvents] = useState<CalendarEventWithContext[]>([])
  const [selectedContextId, setSelectedContextId] = useState<string>('todos')
  const [selectedEvent, setSelectedEvent] = useState<CalendarEventWithContext | null>(null)

  // UI
  const [viewMode, setViewMode] = useState<ViewMode>('mes')
  const [modalOpen, setModalOpen] = useState(false)
  const [editingEvent, setEditingEvent] = useState<CalendarEventWithContext | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<CalendarEventWithContext | null>(null)
  const [statusMsg, setStatusMsg] = useState<{ text: string; ok: boolean } | null>(null)

  function showStatus(text: string, ok = true) {
    setStatusMsg({ text, ok })
    setTimeout(() => setStatusMsg(null), 4000)
  }

  // Load events from the backend (the source of truth)
  const reloadEvents = useCallback(() => {
    apiFetch<{ events: CalendarEventWithContext[] }>('/api/v1/calendar/events')
      .then((d) => setEvents(d.events ?? []))
      .catch(() => setEvents([]))
  }, [])

  useEffect(() => {
    reloadEvents()
  }, [reloadEvents])

  // Filtered events by context
  const filteredEvents = selectedContextId === 'todos'
    ? events
    : events.filter((ev) => ev.context_id === selectedContextId)

  // Build the backend payload from the form (maps description→title, combines date+time)
  const toEventBody = (data: EventFormData, ctxId: string | undefined) => {
    const date = data.startTime ? `${data.date}T${data.startTime}` : data.date
    const endsAt = data.endTime ? `${data.date}T${data.endTime}` : undefined
    return {
      title: data.description,
      date,
      type: data.type,
      location: data.location || undefined,
      endsAt,
      context_id: ctxId,
    }
  }

  // Create / edit event — persist to backend, surface errors, then reload
  const handleSave = useCallback(async (data: EventFormData, eventId?: string) => {
    // Prefer the context chosen in the modal; fall back to the page selector
    const ctxId = data.contextId || (selectedContextId !== 'todos' ? selectedContextId : undefined)
    const body = toEventBody(data, ctxId)
    try {
      if (eventId) {
        await apiFetch(`/api/v1/calendar/events/${eventId}`, {
          method: 'PUT', body: JSON.stringify(body),
        })
        showStatus('Evento actualizado com sucesso.')
      } else {
        await apiFetch('/api/v1/calendar/events', {
          method: 'POST', body: JSON.stringify(body),
        })
        showStatus('Evento criado com sucesso.')
      }
      setModalOpen(false)
      setEditingEvent(null)
      reloadEvents()
    } catch (err) {
      showStatus(err instanceof Error ? err.message : 'Erro ao guardar o evento.', false)
    }
  }, [selectedContextId, reloadEvents])

  // T10 — Delete
  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteTarget) return
    try {
      await apiFetch(`/api/v1/calendar/events/${deleteTarget.id}`, { method: 'DELETE' })
      setEvents((prev) => prev.filter((ev) => ev.id !== deleteTarget.id))
      if (selectedEvent?.id === deleteTarget.id) setSelectedEvent(null)
      showStatus('Evento eliminado.')
    } catch (err) {
      showStatus(err instanceof Error ? err.message : 'Erro ao eliminar o evento.', false)
    } finally {
      setDeleteTarget(null)
    }
  }, [deleteTarget, selectedEvent])

  function openCreate() {
    setEditingEvent(null)
    setModalOpen(true)
  }

  function openEdit(ev: CalendarEvent) {
    setEditingEvent(ev as CalendarEventWithContext)
    setModalOpen(true)
  }

  // 7-day upcoming for bottom panel
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const limit7 = new Date(today)
  limit7.setDate(limit7.getDate() + 7)
  const next7Events = filteredEvents.filter((ev) => {
    const d = new Date(ev.date + 'T00:00:00')
    return d >= today && d <= limit7
  })

  return (
    <div className="min-h-screen bg-background">
      <AppHeader activeTab="calendario" />

      <main className="max-w-[1280px] mx-auto px-6 py-6 flex flex-col gap-5">

        {/* Title + Toolbar — AC1 */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <h1 className="text-xl font-bold text-foreground">Calendário Académico</h1>
          <div className="flex flex-wrap items-center gap-2">
            {/* View switcher — T13, AC5 */}
            <div
              role="tablist"
              aria-label="Vista do calendário"
              className="flex rounded-md border border-border overflow-hidden bg-card"
            >
              {(['mes', 'lista'] as ViewMode[]).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  role="tab"
                  aria-selected={viewMode === mode}
                  onClick={() => setViewMode(mode)}
                  className={[
                    'px-3 py-1.5 text-sm font-medium transition-colors',
                    viewMode === mode
                      ? 'bg-primary text-white'
                      : 'text-muted-foreground hover:bg-muted/50',
                  ].join(' ')}
                >
                  {mode === 'mes' ? 'Mês' : 'Lista'}
                </button>
              ))}
            </div>

            {/* Export — T11, AC12 */}
            <button
              type="button"
              onClick={() => downloadIcs(filteredEvents)}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted/50 transition-colors"
            >
              📤 Exportar ▾
            </button>

            {/* Add event — professor only — AC1 */}
            <button
              type="button"
              onClick={openCreate}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              + Adicionar Evento
            </button>
          </div>
        </div>

        {/* Context selector — T4, AC2 */}
        <div className="flex items-center gap-2">
          <label htmlFor="ctx-select" className="text-sm text-muted-foreground whitespace-nowrap">
            Contexto:
          </label>
          <select
            id="ctx-select"
            value={selectedContextId}
            onChange={(e) => setSelectedContextId(e.target.value)}
            className="border border-border rounded-md px-3 py-1.5 text-sm bg-card focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="todos">Todos os contextos</option>
            {contextOptions.map((ctx) => (
              <option key={ctx.id} value={ctx.id}>{ctx.label}</option>
            ))}
          </select>
        </div>

        {/* Status message */}
        {statusMsg && (
          <div
            role="status"
            aria-live="polite"
            className={[
              'rounded-md px-4 py-2.5 text-sm font-medium',
              statusMsg.ok
                ? 'bg-success/10 border border-success/20 text-success'
                : 'bg-destructive/10 border border-destructive/20 text-destructive',
            ].join(' ')}
          >
            {statusMsg.text}
          </div>
        )}

        {/* Main 2-col layout: calendar (70%) + sidebar (30%) */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-5">
          {/* Left column: calendar + upcoming */}
          <div className="flex flex-col gap-5">
            {viewMode === 'mes' ? (
              // T2 — MonthCalendar with allowEdit + onEventClick — AC3, AC4, AC13
              <MonthCalendar
                events={filteredEvents}
                allowEdit
                onEventClick={(ev) => setSelectedEvent((prev) => prev?.id === ev.id ? null : ev)}
                selectedEventId={selectedEvent?.id ?? null}
              />
            ) : (
              // T3 — List view — AC5
              <ListViewPanel events={filteredEvents} />
            )}

            {/* AC7 — Próximos 7 dias */}
            <div>
              <h2 className="text-sm font-semibold text-foreground mb-2">
                Próximos Eventos (7 dias)
              </h2>
              <UpcomingEventsList events={next7Events} />
            </div>
          </div>

          {/* Right sidebar: legend + event detail — T5, T12, AC6, AC14 */}
          <EventDetailPanel
            event={selectedEvent}
            role="professor"
            onEdit={openEdit}
            onDelete={(ev) => setDeleteTarget(ev as CalendarEventWithContext)}
            onClose={() => setSelectedEvent(null)}
          />
        </div>
      </main>

      {/* T6, T7 — Create / Edit modal — AC8, AC9 */}
      <EventModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        event={editingEvent}
        contexts={contextOptions}
        onSave={handleSave}
      />

      {/* T10 — Delete confirmation dialog — AC10 */}
      <Dialog
        open={!!deleteTarget}
        onOpenChange={(o) => { if (!o) setDeleteTarget(null) }}
      >
        <DialogContent aria-labelledby="delete-dialog-title">
          <DialogHeader>
            <DialogTitle id="delete-dialog-title">Eliminar evento</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Eliminar o evento{' '}
            <strong>"{deleteTarget?.title}"</strong>?{' '}
            Esta acção não pode ser desfeita.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
              Cancelar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
            >
              Eliminar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
