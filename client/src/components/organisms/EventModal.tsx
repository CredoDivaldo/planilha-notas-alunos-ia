// EventModal — create/edit calendar event modal for professor
// Story 7.8 — T6, T7

import { useState, useEffect, useId } from 'react'
import { Pencil, Calendar } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import type { EventType, CalendarEvent } from '@/components/molecules/EventDot'

// ---------------------------------------------------------------------------
// Event type configuration
// ---------------------------------------------------------------------------
export interface EventTypeConfig {
  value: EventType
  label: string
  color: string
  hex: string
}

export const EVENT_TYPE_OPTIONS: EventTypeConfig[] = [
  { value: 'exame',   label: 'Prova',       color: 'bg-blue-500',   hex: '#3B82F6' },
  { value: 'outro',   label: 'Exame',       color: 'bg-purple-500', hex: '#8B5CF6' },
  { value: 'recurso', label: 'Recurso',     color: 'bg-orange-400', hex: '#F97316' },
  { value: 'entrega', label: 'Entrega',     color: 'bg-green-500',  hex: '#22C55E' },
  { value: 'feriado', label: 'Prova Extra', color: 'bg-red-400',    hex: '#EF4444' },
]

// ---------------------------------------------------------------------------
// Event form data
// ---------------------------------------------------------------------------
export interface EventFormData {
  type: EventType
  description: string
  contextId: string
  date: string
  startTime: string
  endTime: string
  location: string
  notes: string
  visivelEstudantes: boolean
}

const EMPTY_FORM: EventFormData = {
  type: 'exame',
  description: '',
  contextId: '',
  date: '',
  startTime: '',
  endTime: '',
  location: '',
  notes: '',
  visivelEstudantes: true,
}

// ---------------------------------------------------------------------------
// Context option type (for selector)
// ---------------------------------------------------------------------------
export interface ContextOption {
  id: string
  label: string
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------
interface EventModalProps {
  open: boolean
  onClose: () => void
  /** If provided, modal is in edit mode with pre-filled data */
  event?: CalendarEvent | null
  contexts: ContextOption[]
  onSave: (data: EventFormData, eventId?: string) => Promise<void>
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function eventToForm(ev: CalendarEvent): EventFormData {
  const timeParts = ev.time?.includes('–') ? ev.time.split('–') : [ev.time ?? '', '']
  return {
    type: ev.type,
    description: ev.title,
    contextId: '',
    date: ev.date,
    startTime: timeParts[0]?.trim() ?? '',
    endTime: timeParts[1]?.trim() ?? '',
    location: ev.location ?? '',
    notes: ev.description ?? '',
    visivelEstudantes: true,
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export function EventModal({ open, onClose, event, contexts, onSave }: EventModalProps) {
  const titleId = useId()
  const isEdit = !!event
  const [form, setForm] = useState<EventFormData>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Populate form when event changes
  useEffect(() => {
    if (open) {
      setForm(event ? eventToForm(event) : EMPTY_FORM)
      setError(null)
    }
  }, [open, event])

  function setField<K extends keyof EventFormData>(key: K, value: EventFormData[K]) {
    setForm(prev => ({ ...prev, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.description.trim()) { setError('A descrição é obrigatória.'); return }
    if (!form.date) { setError('A data é obrigatória.'); return }
    setSaving(true)
    setError(null)
    try {
      await onSave(form, event?.id)
      onClose()
    } catch {
      setError('Erro ao guardar evento. Tente novamente.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose() }}>
      <DialogContent
        className="max-w-lg max-h-[90vh] overflow-y-auto"
        aria-labelledby={titleId}
      >
        <DialogHeader>
          <DialogTitle id={titleId}>
            {isEdit ? <><Pencil className="size-4" /> Editar Evento Académico</> : <><Calendar className="size-4" /> Criar Evento Académico</>}
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-2">
          {/* T7 — RadioGroup for event type */}
          <fieldset>
            <legend className="text-sm font-medium text-foreground mb-2">
              Tipo de evento <span className="text-destructive">*</span>
            </legend>
            <RadioGroup
              value={form.type}
              onValueChange={(v) => setField('type', v as EventType)}
              role="radiogroup"
              aria-required="true"
              className="grid grid-cols-1 gap-2"
            >
              {EVENT_TYPE_OPTIONS.map((opt) => (
                <div key={opt.value} className="flex items-center gap-3">
                  <RadioGroupItem value={opt.value} id={`type-${opt.value}`} />
                  <Label
                    htmlFor={`type-${opt.value}`}
                    className="flex items-center gap-2 cursor-pointer text-sm"
                  >
                    <span
                      className={`inline-block w-3 h-3 rounded-full ${opt.color}`}
                      aria-hidden="true"
                    />
                    <span>{opt.label}</span>
                    <span className="text-xs text-muted-foreground">{opt.hex}</span>
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </fieldset>

          {/* Description */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="event-desc">
              Descrição <span className="text-destructive">*</span>
            </Label>
            <Input
              id="event-desc"
              value={form.description}
              onChange={(e) => setField('description', e.target.value)}
              placeholder="Ex: Exame Final Inglês Técnico"
              required
            />
          </div>

          {/* Context */}
          {contexts.length > 0 && (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="event-context">
                Contexto <span className="text-destructive">*</span>
              </Label>
              <select
                id="event-context"
                value={form.contextId}
                onChange={(e) => setField('contextId', e.target.value)}
                className="border border-border rounded-md px-3 py-2 text-sm bg-card focus:outline-none focus:ring-1 focus:ring-ring"
                required
              >
                <option value="">Seleccionar contexto…</option>
                {contexts.map((ctx) => (
                  <option key={ctx.id} value={ctx.id}>{ctx.label}</option>
                ))}
              </select>
            </div>
          )}

          {/* Date */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="event-date">
              Data <span className="text-destructive">*</span>
            </Label>
            <Input
              id="event-date"
              type="date"
              value={form.date}
              onChange={(e) => setField('date', e.target.value)}
              required
            />
          </div>

          {/* Time range */}
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="event-start">Hora início</Label>
              <Input
                id="event-start"
                type="time"
                value={form.startTime}
                onChange={(e) => setField('startTime', e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="event-end">Hora fim</Label>
              <Input
                id="event-end"
                type="time"
                value={form.endTime}
                onChange={(e) => setField('endTime', e.target.value)}
              />
            </div>
          </div>

          {/* Location */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="event-location">Local</Label>
            <Input
              id="event-location"
              value={form.location}
              onChange={(e) => setField('location', e.target.value)}
              placeholder="Ex: Sala 3"
            />
          </div>

          {/* Notes */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="event-notes">Notas internas (facultativo)</Label>
            <textarea
              id="event-notes"
              value={form.notes}
              onChange={(e) => setField('notes', e.target.value)}
              rows={2}
              placeholder="Notas visíveis apenas para o professor…"
              className="border border-border rounded-md px-3 py-2 text-sm bg-card focus:outline-none focus:ring-1 focus:ring-ring resize-none"
            />
          </div>

          {/* Visible for students toggle */}
          <div className="flex items-center gap-3 py-1">
            <button
              type="button"
              role="switch"
              aria-checked={form.visivelEstudantes}
              onClick={() => setField('visivelEstudantes', !form.visivelEstudantes)}
              className={[
                'relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-ring',
                form.visivelEstudantes ? 'bg-primary' : 'bg-muted-foreground',
              ].join(' ')}
            >
              <span
                className={[
                  'inline-block h-3.5 w-3.5 rounded-full bg-card shadow transition-transform',
                  form.visivelEstudantes ? 'translate-x-4' : 'translate-x-0.5',
                ].join(' ')}
              />
            </button>
            <span className="text-sm text-foreground">
              Visível para estudantes:{' '}
              <strong>{form.visivelEstudantes ? 'Sim' : 'Não'}</strong>
            </span>
          </div>

          {/* Error */}
          {error && (
            <p role="alert" className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md px-3 py-2">
              {error}
            </p>
          )}

          <DialogFooter className="mt-2">
            <Button type="button" variant="outline" onClick={onClose} disabled={saving}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? 'A guardar…' : isEdit ? 'Guardar alterações' : 'Criar evento'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
