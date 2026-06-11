import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'
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
    delegado: null,
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
]

interface ActiveContextType {
  contexts: ContextItem[]
  activeContextId: string | null
  activeContext: ContextItem | null
  setActiveContextId: (id: string) => void
  reloadContexts: () => void
}

const ActiveContextContext = createContext<ActiveContextType | null>(null)

export function ActiveContextProvider({ children }: { children: ReactNode }) {
  const [contexts, setContexts] = useState<ContextItem[]>([])
  const [activeContextId, setActiveContextIdState] = useState<string | null>(
    () => sessionStorage.getItem('active_context_id'),
  )

  const reloadContexts = useCallback(() => {
    apiFetch<ContextItem[]>('/academic-contexts/')
      .then((data) => {
        setContexts(data)
        setActiveContextIdState((prev) => {
          if (prev && data.some((c) => c.id === prev)) return prev
          const firstId = data[0]?.id ?? null
          if (firstId) sessionStorage.setItem('active_context_id', firstId)
          return firstId
        })
      })
      .catch(() => {
        setContexts(MOCK_CONTEXTS)
        setActiveContextIdState((prev) => {
          if (prev && MOCK_CONTEXTS.some((c) => c.id === prev)) return prev
          const firstId = MOCK_CONTEXTS[0]?.id ?? null
          if (firstId) sessionStorage.setItem('active_context_id', firstId)
          return firstId
        })
      })
  }, [])

  useEffect(() => {
    reloadContexts()
  }, [reloadContexts])

  const setActiveContextId = useCallback((id: string) => {
    setActiveContextIdState(id)
    sessionStorage.setItem('active_context_id', id)
  }, [])

  const activeContext = contexts.find((c) => c.id === activeContextId) ?? null

  return (
    <ActiveContextContext.Provider
      value={{ contexts, activeContextId, activeContext, setActiveContextId, reloadContexts }}
    >
      {children}
    </ActiveContextContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useActiveContext() {
  const ctx = useContext(ActiveContextContext)
  if (!ctx) throw new Error('useActiveContext must be used within ActiveContextProvider')
  return ctx
}
