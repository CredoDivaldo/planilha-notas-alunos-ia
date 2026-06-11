// EventDot — coloured dot for calendar events, with tooltip on click/hover
// T4: prerequisite for MonthCalendar

export type EventType = 'exame' | 'recurso' | 'entrega' | 'reuniao' | 'feriado' | 'outro'

export interface CalendarEvent {
  id: string
  date: string          // ISO date string YYYY-MM-DD
  type: EventType
  title: string
  time?: string         // e.g. "09:00"
  location?: string
  description?: string
}

const EVENT_COLOR: Record<EventType, string> = {
  exame:    'bg-blue-500',
  recurso:  'bg-orange-400',
  entrega:  'bg-purple-500',
  reuniao:  'bg-green-500',
  feriado:  'bg-red-400',
  outro:    'bg-muted-foreground',
}

const EVENT_COLOR_TEXT: Record<EventType, string> = {
  exame:    'text-blue-700 bg-blue-50 border-blue-200',
  recurso:  'text-orange-700 bg-orange-50 border-orange-200',
  entrega:  'text-purple-700 bg-purple-50 border-purple-200',
  reuniao:  'text-green-700 bg-green-50 border-green-200',
  feriado:  'text-red-700 bg-red-50 border-red-200',
  outro:    'text-muted-foreground bg-muted border-border',
}

// eslint-disable-next-line react-refresh/only-export-components
export function eventColorClass(type: EventType): string {
  return EVENT_COLOR[type] ?? EVENT_COLOR.outro
}

// eslint-disable-next-line react-refresh/only-export-components
export function eventColorTextClass(type: EventType): string {
  return EVENT_COLOR_TEXT[type] ?? EVENT_COLOR_TEXT.outro
}

interface EventDotProps {
  event: CalendarEvent
  /** show tooltip label, default true */
  showTooltip?: boolean
}

export function EventDot({ event, showTooltip = true }: EventDotProps) {
  const label = [
    event.date,
    event.title,
    event.time,
    event.location,
  ].filter(Boolean).join(' · ')

  return (
    <button
      type="button"
      title={showTooltip ? label : undefined}
      aria-label={label}
      className={[
        'inline-block w-2 h-2 rounded-full cursor-pointer',
        'focus:outline-none focus:ring-2 focus:ring-offset-1 focus:ring-current',
        'hover:scale-125 transition-transform',
        eventColorClass(event.type),
      ].join(' ')}
    />
  )
}
