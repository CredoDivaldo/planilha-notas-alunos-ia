// StudentPortalLayout — wraps the student portal with a student-specific header (AC2)
// T1/T2: layout scaffold; AppHeader-variant with student name + number + logout

import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import type { ReactNode } from 'react'

interface StudentPortalLayoutProps {
  children: ReactNode
  studentNumber?: string
}

export function StudentPortalLayout({ children, studentNumber }: StudentPortalLayoutProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* AC2: Header with "📊 Portal do Estudante", student name, number, logout */}
      <header className="bg-white border-b border-slate-200 px-4 sm:px-6 h-14 flex items-center justify-between shrink-0">
        <span className="font-semibold text-[#0D6EFD] text-base select-none">
          📊 Portal do Estudante
        </span>
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="text-sm text-slate-700 hidden sm:inline">
            👤 {user?.name ?? 'Estudante'}
          </span>
          {studentNumber && (
            <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
              {studentNumber}
            </span>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            className="min-w-[44px] min-h-[44px]"
          >
            Sair
          </Button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 w-full max-w-[1280px] mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>
    </div>
  )
}
