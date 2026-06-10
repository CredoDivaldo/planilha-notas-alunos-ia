import { useEffect, useRef, useState, useId } from 'react'
import { Pencil, Trash2, AlertTriangle, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { ContextItem, GradeComponent } from '@/types'

interface ComponentRow {
  id: string
  name: string
  weight: string
}

type ModalMode = 'create' | 'edit'

interface ContextModalProps {
  isOpen: boolean
  mode: ModalMode
  initialData?: ContextItem | null
  onClose: () => void
  onSubmit: (payload: ContextPayload) => Promise<void>
}

export interface ContextPayload {
  turma: string
  disciplina: string
  semestre: string
  turno: string
  curso?: string
  components: { name: string; weight: number }[]
}

const DISCIPLINAS = [
  'Inglês Técnico',
  'Matemática',
  'Física',
  'Química',
  'Programação',
  'Redes de Computadores',
  'Base de Dados',
  'Gestão de Projectos',
]

const SEMESTRES = ['2026/1', '2026/2', '2025/1', '2025/2', '2024/1', '2024/2']

const TURNOS = ['Manhã', 'Tarde', 'Noite']

const CURSOS = [
  'Engenharia Informática',
  'Engenharia Electrónica',
  'Gestão Empresarial',
  'Direito',
  'Medicina',
]

function makeRow(): ComponentRow {
  return { id: crypto.randomUUID(), name: '', weight: '' }
}

function fromGradeComponents(comps: GradeComponent[]): ComponentRow[] {
  return comps.map((c) => ({ id: c.id, name: c.name, weight: String(c.weight) }))
}

export function ContextModal({
  isOpen,
  mode,
  initialData,
  onClose,
  onSubmit,
}: ContextModalProps) {
  const titleId = useId()
  const dialogRef = useRef<HTMLDivElement>(null)

  // Modal returns null when !isOpen, so these lazy initializers run fresh on each open
  const [turma, setTurma] = useState(() =>
    mode === 'edit' && initialData ? initialData.turma : ''
  )
  const [disciplina, setDisciplina] = useState(() =>
    mode === 'edit' && initialData ? initialData.disciplina : ''
  )
  const [semestre, setSemestre] = useState(() =>
    mode === 'edit' && initialData ? initialData.semestre : ''
  )
  const [turno, setTurno] = useState(() =>
    mode === 'edit' && initialData ? initialData.turno : ''
  )
  const [curso, setCurso] = useState('')
  const [components, setComponents] = useState<ComponentRow[]>(() =>
    mode === 'edit' && initialData && initialData.components.length > 0
      ? fromGradeComponents(initialData.components)
      : [makeRow()]
  )
  const [submitting, setSubmitting] = useState(false)
  const [backendError, setBackendError] = useState<string | null>(null)

  // Focus trap + Escape handler
  useEffect(() => {
    if (!isOpen) return
    const el = dialogRef.current
    if (!el) return

    const focusable = el.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    )
    focusable[0]?.focus()

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
        return
      }
      if (e.key === 'Tab') {
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault()
          last?.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault()
          first?.focus()
        }
      }
    }

    el.addEventListener('keydown', handleKeyDown)
    return () => el.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const totalWeight = components.reduce((sum, c) => sum + Number(c.weight || 0), 0)
  const isWeightValid = Math.abs(totalWeight - 100) < 0.01
  const hasComponents = components.length > 0 && components.some((c) => c.name || c.weight)
  const isFormValid = turma.trim() !== '' && disciplina !== '' && semestre !== '' && turno !== ''

  const handleAddComponent = () => {
    setComponents((prev) => [...prev, makeRow()])
  }

  const handleRemoveComponent = (id: string) => {
    setComponents((prev) => prev.filter((c) => c.id !== id))
  }

  const handleComponentChange = (id: string, field: 'name' | 'weight', value: string) => {
    setComponents((prev) =>
      prev.map((c) => (c.id === id ? { ...c, [field]: value } : c)),
    )
  }

  const handleSubmit = async () => {
    if (!isFormValid) return
    if (hasComponents && !isWeightValid) return

    const payload: ContextPayload = {
      turma: turma.trim(),
      disciplina,
      semestre,
      turno,
      ...(curso ? { curso } : {}),
      components: components
        .filter((c) => c.name.trim())
        .map((c) => ({ name: c.name.trim(), weight: Number(c.weight) })),
    }

    setSubmitting(true)
    setBackendError(null)
    try {
      await onSubmit(payload)
    } catch (err) {
      setBackendError(err instanceof Error ? err.message : 'Erro desconhecido')
    } finally {
      setSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    // Backdrop
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      {/* Dialog */}
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="bg-card rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 id={titleId} className="text-lg font-semibold text-foreground">
            {mode === 'create' ? <><Pencil className="size-4 mr-1" /> Criar Contexto Académico</> : <><Pencil className="size-4 mr-1" /> Editar Contexto Académico</>}
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar modal"
            className="text-muted-foreground hover:text-foreground transition-colors p-1 rounded"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 flex flex-col gap-4">
          {/* Turma */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ctx-turma">
              Turma <span className="text-destructive">*</span>
            </Label>
            <Input
              id="ctx-turma"
              value={turma}
              onChange={(e) => setTurma(e.target.value)}
              placeholder="Ex: ING-T1"
              required
            />
          </div>

          {/* Disciplina */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ctx-disciplina">
              Disciplina <span className="text-destructive">*</span>
            </Label>
            <Select value={disciplina} onValueChange={setDisciplina}>
              <SelectTrigger id="ctx-disciplina" className="w-full">
                <SelectValue placeholder="Seleccionar disciplina" />
              </SelectTrigger>
              <SelectContent>
                {DISCIPLINAS.map((d) => (
                  <SelectItem key={d} value={d}>{d}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Semestre */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ctx-semestre">
              Semestre <span className="text-destructive">*</span>
            </Label>
            <Select value={semestre} onValueChange={setSemestre}>
              <SelectTrigger id="ctx-semestre" className="w-full">
                <SelectValue placeholder="Seleccionar semestre" />
              </SelectTrigger>
              <SelectContent>
                {SEMESTRES.map((s) => (
                  <SelectItem key={s} value={s}>{s}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Turno */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ctx-turno">
              Turno <span className="text-destructive">*</span>
            </Label>
            <Select value={turno} onValueChange={setTurno}>
              <SelectTrigger id="ctx-turno" className="w-full">
                <SelectValue placeholder="Seleccionar turno" />
              </SelectTrigger>
              <SelectContent>
                {TURNOS.map((t) => (
                  <SelectItem key={t} value={t}>{t}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Curso (optional) */}
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="ctx-curso">Curso</Label>
            <Select value={curso} onValueChange={setCurso}>
              <SelectTrigger id="ctx-curso" className="w-full">
                <SelectValue placeholder="Seleccionar curso (opcional)" />
              </SelectTrigger>
              <SelectContent>
                {CURSOS.map((c) => (
                  <SelectItem key={c} value={c}>{c}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Componentes de Avaliação */}
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-2">
              Componentes de Avaliação
            </h3>

            {components.length > 0 && (
              <table className="w-full text-sm mb-2" aria-label="Componentes de avaliação">
                <thead>
                  <tr className="border-b border-border">
                    <th scope="col" className="text-left pb-1 font-medium text-slate-600">Componente</th>
                    <th scope="col" className="text-left pb-1 font-medium text-slate-600 w-24">Peso (%)</th>
                    <th scope="col" className="w-10 pb-1" aria-label="Remover" />
                  </tr>
                </thead>
                <tbody>
                  {components.map((row) => (
                    <tr key={row.id} className="border-b border-slate-100">
                      <td className="py-1.5 pr-2">
                        <Input
                          value={row.name}
                          onChange={(e) => handleComponentChange(row.id, 'name', e.target.value)}
                          placeholder="Ex: Frequência"
                          aria-label="Nome do componente"
                          className="h-8 text-sm"
                        />
                      </td>
                      <td className="py-1.5 pr-2">
                        <Input
                          type="number"
                          min="0"
                          max="100"
                          value={row.weight}
                          onChange={(e) => handleComponentChange(row.id, 'weight', e.target.value)}
                          placeholder="0"
                          aria-label="Peso percentual"
                          className="h-8 text-sm"
                        />
                      </td>
                      <td className="py-1.5">
                        <button
                          type="button"
                          onClick={() => handleRemoveComponent(row.id)}
                          aria-label={`Remover componente ${row.name || ''}`}
                          className="text-destructive hover:text-destructive/80 transition-colors"
                        >
                          <Trash2 className="size-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {/* Total row */}
                  <tr>
                    <td className="pt-1.5 font-medium text-foreground">Total</td>
                    <td className={['pt-1.5 font-semibold', isWeightValid ? 'text-success' : 'text-warning'].join(' ')}>
                      {totalWeight}%
                    </td>
                    <td />
                  </tr>
                </tbody>
              </table>
            )}

            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleAddComponent}
              className="text-primary border-primary hover:bg-primary/5"
            >
              + Componente
            </Button>

            {/* Weight warning */}
            {hasComponents && !isWeightValid && (
              <div
                role="alert"
                aria-live="polite"
                className="mt-2 flex items-center gap-2 rounded bg-warning/10 border border-warning/20 px-3 py-2 text-sm text-warning"
              >
                <AlertTriangle className="size-4 shrink-0" /> Os pesos devem somar 100%. Actual: {totalWeight}%
              </div>
            )}
          </div>

          {/* Backend error */}
          {backendError && (
            <div
              role="alert"
              className="rounded bg-destructive/10 border border-destructive/20 px-3 py-2 text-sm text-destructive"
            >
              {backendError}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Cancelar
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isFormValid || (hasComponents && !isWeightValid) || submitting}
            className="bg-primary hover:bg-primary/90 text-white"
          >
            {submitting
              ? 'A guardar…'
              : mode === 'create'
              ? 'Criar Contexto'
              : 'Guardar Alterações'}
          </Button>
        </div>
      </div>
    </div>
  )
}
