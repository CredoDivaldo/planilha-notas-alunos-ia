// StudentPortalLayout — wraps the student portal with a student-specific header (AC2)
// T1/T2: layout scaffold; AppHeader-variant with student name + number + logout

import { useNavigate } from 'react-router-dom'
import { User, LayoutDashboard } from 'lucide-react'
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
    <div className="min-h-screen bg-muted/50 flex flex-col">
      {/* AC2: Header with "📊 Portal do Estudante", student name, number, logout */}
      <header className="bg-card border-b border-border px-4 sm:px-6 h-14 flex items-center justify-between shrink-0">
        <span className="font-semibold text-primary text-base select-none">
          <span className="flex items-center gap-2"><LayoutDashboard className="size-4" /> Portal do Estudante</span>
        </span>
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="text-sm text-foreground hidden sm:inline">
            <span className="flex items-center gap-1.5"><User className="size-4" /> {user?.name ?? 'Estudante'}</span>
          </span>
          {studentNumber && (
            <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">
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
