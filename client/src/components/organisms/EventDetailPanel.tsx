// EventDetailPanel — sidebar right panel with event detail + role-conditional buttons
// Story 7.8 — T5, AC6, AC14

import type { CalendarEvent, EventType } from '@/components/molecules/EventDot'
import { eventColorTextClass } from '@/components/molecules/EventDot'
import { EVENT_TYPE_OPTIONS } from './EventModal'

// ---------------------------------------------------------------------------
// Colour legend (T12 / AC14) — inlined here as per story scope
// ---------------------------------------------------------------------------
function ColorLegend() {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
        Legenda de cores
      </h3>
      <div className="flex flex-col gap-2">
        {EVENT_TYPE_OPTIONS.map((opt) => (
          <div key={opt.value} className="flex items-center gap-2 text-xs text-slate-700">
            <span
              className={`inline-block w-3 h-3 rounded-full shrink-0 ${opt.color}`}
              aria-hidden="true"
            />
            <span>{opt.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Event type label helper
// ---------------------------------------------------------------------------
function eventTypeLabel(type: EventType): string {
  return EVENT_TYPE_OPTIONS.find((o) => o.value === type)?.label ?? type
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface EventDetailPanelProps {
  event: CalendarEvent | null
  role: 'professor' | 'estudante' | 'delegado' | null
  onEdit?: (event: CalendarEvent) => void
  onDelete?: (event: CalendarEvent) => void
  onClose?: () => void
}

// ---------------------------------------------------------------------------
// Main panel
// ---------------------------------------------------------------------------
export function EventDetailPanel({
  event,
  role,
  onEdit,
  onDelete,
  onClose,
}: EventDetailPanelProps) {
  const isProfessor = role === 'professor'

  return (
    <aside className="flex flex-col gap-4" aria-label="Painel de detalhe do evento">
      {/* Colour legend always visible — AC14 */}
      <ColorLegend />

      {/* Event detail — shown when an event is selected */}
      {event ? (
        <div className="bg-white rounded-lg border border-slate-200 p-4 flex flex-col gap-3">
          {/* Header with close */}
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-sm font-semibold text-slate-800 leading-snug">
              {event.title}
            </h3>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                aria-label="Fechar detalhe do evento"
                className="text-slate-400 hover:text-slate-600 transition-colors text-base leading-none shrink-0"
              >
                ×
              </button>
            )}
          </div>

          {/* Type badge */}
          <span
            className={[
              'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium w-fit',
              eventColorTextClass(event.type),
            ].join(' ')}
          >
            {eventTypeLabel(event.type)}
          </span>

          {/* Details */}
          <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5 text-xs text-slate-600">
            <dt className="font-medium text-slate-500">Data</dt>
            <dd>{event.date}</dd>

            {event.time && (
              <>
                <dt className="font-medium text-slate-500">Horário</dt>
                <dd>{event.time}</dd>
              </>
            )}

            {event.location && (
              <>
                <dt className="font-medium text-slate-500">Local</dt>
                <dd>{event.location}</dd>
              </>
            )}

            {event.description && (
              <>
                <dt className="font-medium text-slate-500">Notas</dt>
                <dd>{event.description}</dd>
              </>
            )}
          </dl>

          {/* Professor actions — AC6 */}
          {isProfessor && (
            <div className="flex gap-2 mt-1 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => onEdit?.(event)}
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-md border border-slate-300 bg-white text-xs font-medium text-slate-700 hover:bg-slate-50 transition-colors"
              >
                ✏️ Editar evento
              </button>
              <button
                type="button"
                onClick={() => onDelete?.(event)}
                className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-md border border-red-200 bg-red-50 text-xs font-medium text-red-700 hover:bg-red-100 transition-colors"
              >
                🗑 Eliminar
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <p className="text-xs text-slate-400 text-center">
            Clique num evento para ver o detalhe
          </p>
        </div>
      )}
    </aside>
  )
}
