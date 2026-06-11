import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { apiFetch } from '@/lib/api'
import type { ContextItem } from '@/types'

const MOCK_CONTEXTS: ContextItem[] = [
  {
    id: '1',
    turma: 'ING-T1',
    disciplina: 'Inglês Técnico',
    semestre: '2026/1',
    turno: 'Manhã',
    alunosCount: 42,
    delegado: { id: 'a1', name: 'Carlos Mendes', studentNumber: '22009' },
    components: [
      { id: 'c1', name: 'Frequência', weight: 40 },
      { id: 'c2', name: 'Exame Final', weight: 60 },
    ],
  },
  {
    id: '2',
    turma: 'ING-T2',
    disciplina: 'Inglês Técnico',
    semestre: '2026/1',
    turno: 'Tarde',
    alunosCount: 38,
    delegado: null,
    components: [],
  },
  {
    id: '3',
    turma: 'MAT-T1',
    disciplina: 'Matemática',
    semestre: '2026/1',
    turno: 'Manhã',
    alunosCount: 40,
    delegado: null,
    components: [],
  },
]

interface ContextBarProps {
  onContextChange?: (contextId: string) => void
}

export function ContextBar({ onContextChange }: ContextBarProps) {
  const navigate = useNavigate()
  const [contexts, setContexts] = useState<ContextItem[]>([])
  const [activeContextId, setActiveContextId] = useState<string>(() => {
    return sessionStorage.getItem('active_context_id') ?? ''
  })
  // Track whether we've set a default yet so the fetch callback can do it once
  const defaultSetRef = useRef(false)

  useEffect(() => {
    apiFetch<ContextItem[]>('/academic-contexts/')
      .then((data) => {
        setContexts(data)
        if (!defaultSetRef.current && data.length > 0 && !sessionStorage.getItem('active_context_id')) {
          defaultSetRef.current = true
          const firstId = data[0].id
          setActiveContextId(firstId)
          sessionStorage.setItem('active_context_id', firstId)
          onContextChange?.(firstId)
        }
      })
      .catch(() => {
        setContexts(MOCK_CONTEXTS)
        if (!defaultSetRef.current && !sessionStorage.getItem('active_context_id') && MOCK_CONTEXTS.length > 0) {
          defaultSetRef.current = true
          const firstId = MOCK_CONTEXTS[0].id
          setActiveContextId(firstId)
          sessionStorage.setItem('active_context_id', firstId)
          onContextChange?.(firstId)
        }
      })
  // onContextChange intentionally omitted — stable callback reference expected
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleChange = (value: string) => {
    setActiveContextId(value)
    sessionStorage.setItem('active_context_id', value)
    onContextChange?.(value)
  }

  return (
    <div className="bg-muted/50 border-b border-border px-6 py-2 flex items-center gap-3">
      <span className="text-sm text-muted-foreground font-medium whitespace-nowrap">
        Contexto activo:
      </span>
      <Select value={activeContextId} onValueChange={handleChange}>
        <SelectTrigger className="w-64 h-8 text-sm">
          <SelectValue placeholder="Seleccionar contexto…" />
        </SelectTrigger>
        <SelectContent>
          {contexts.map((ctx) => (
            <SelectItem key={ctx.id} value={ctx.id}>
              {ctx.turma} · {ctx.disciplina} · {ctx.semestre}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Button
        variant="outline"
        size="sm"
        className="h-8 text-xs text-primary border-primary hover:bg-primary/5"
        onClick={() => navigate('/contextos')}
      >
        + Novo
      </Button>
    </div>
  )
}
