import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'
import { apiFetch } from '@/lib/api'
import type { ContextItem } from '@/types'

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
        setContexts([])
        // Keep existing active context ID if user had one; don't override with mock
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
