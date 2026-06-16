import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import type { ReactNode } from 'react'
import { apiFetch } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
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
  const { user } = useAuth()
  const userId = user?.id ?? null
  const role = user?.role ?? null

  const [contexts, setContexts] = useState<ContextItem[]>([])
  const [activeContextId, setActiveContextIdState] = useState<string | null>(null)

  const reloadContexts = useCallback(() => {
    // Contexts are a professor concept; clear for non-professors / logged-out.
    if (!userId || role !== 'professor') {
      setContexts([])
      setActiveContextIdState(null)
      return
    }
    apiFetch<ContextItem[]>('/academic-contexts/')
      .then((data) => {
        setContexts(data)
        setActiveContextIdState((prev) => {
          // Keep the current selection only if it belongs to THIS account's list.
          if (prev && data.some((c) => c.id === prev)) return prev
          return data[0]?.id ?? null
        })
      })
      .catch(() => {
        setContexts([])
        setActiveContextIdState(null)
      })
  }, [userId, role])

  // Reload whenever the authenticated user changes (login / logout / switch).
  useEffect(() => {
    reloadContexts()
  }, [reloadContexts])

  const setActiveContextId = useCallback((id: string) => {
    setActiveContextIdState(id)
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
