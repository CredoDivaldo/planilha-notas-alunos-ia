import { Link, useNavigate } from 'react-router-dom'
import { useTheme } from 'next-themes'
import { GraduationCap, Sun, Moon, User, LogOut, BookOpen } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useActiveContext } from '@/contexts/ActiveContextContext'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export type ActiveTab = 'painel' | 'contextos' | 'notas' | 'calendario' | 'publicar'

interface AppHeaderProps {
  activeTab: ActiveTab
}

const NAV_TABS: { id: ActiveTab; label: string; href: string }[] = [
  { id: 'painel', label: 'Painel', href: '/painel' },
  { id: 'contextos', label: 'Contextos', href: '/contextos' },
  { id: 'notas', label: 'Notas', href: '/notas' },
  { id: 'calendario', label: 'Calendário', href: '/calendario' },
  { id: 'publicar', label: 'Publicar', href: '/publicar' },
]

export function AppHeader({ activeTab }: AppHeaderProps) {
  const { user, logout } = useAuth()
  const { theme, setTheme } = useTheme()
  const { contexts, activeContextId, setActiveContextId } = useActiveContext()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  const isProfessor = user?.role === 'professor'

  return (
    <header className="bg-card border-b border-border px-6 h-14 flex items-center justify-between sticky top-0 z-50 backdrop-blur-sm">
      {/* Left: Logo + Nav */}
      <div className="flex items-center gap-6">
        <Link to="/painel" className="flex items-center gap-2 text-primary font-semibold text-base select-none">
          <GraduationCap className="size-5" />
          <span>UniGrade</span>
        </Link>
        <nav aria-label="Navegação principal" className="flex items-center gap-1">
          {NAV_TABS.map((tab) => {
            const isActive = tab.id === activeTab
            return (
              <Link
                key={tab.id}
                to={tab.href}
                aria-current={isActive ? 'page' : undefined}
                className={[
                  'px-3 py-1 text-sm rounded-md transition-colors',
                  isActive
                    ? 'text-primary border-b-2 border-primary font-medium'
                    : 'text-muted-foreground hover:text-foreground',
                ].join(' ')}
              >
                {tab.label}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Centre: Active context selector — professors only */}
      {isProfessor && contexts.length > 0 && (
        <div className="flex items-center gap-2 text-sm">
          <BookOpen className="size-3.5 text-muted-foreground shrink-0" />
          <Select value={activeContextId ?? ''} onValueChange={setActiveContextId}>
            <SelectTrigger className="h-7 text-xs w-52 border-border">
              <SelectValue placeholder="Seleccionar contexto…" />
            </SelectTrigger>
            <SelectContent>
              {contexts.map((ctx) => (
                <SelectItem key={ctx.id} value={ctx.id} className="text-xs">
                  {ctx.turma} · {ctx.disciplina}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Right: Theme toggle + User + Logout */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon-sm"
          aria-label="Alternar tema"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        >
          {theme === 'dark' ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </Button>

        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <User className="size-4" />
          <span>{user?.name ?? 'Utilizador'}</span>
        </div>

        <Button variant="ghost" size="sm" onClick={handleLogout} className="gap-1.5">
          <LogOut className="size-4" />
          <span className="hidden sm:inline">Sair</span>
        </Button>
      </div>
    </header>
  )
}
