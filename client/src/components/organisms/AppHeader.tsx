import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'

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
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="bg-white border-b border-slate-200 px-6 h-14 flex items-center justify-between">
      {/* Left: Logo + Nav */}
      <div className="flex items-center gap-6">
        <span className="font-semibold text-[#0D6EFD] text-base select-none">
          📊 Planilha Notas
        </span>
        <nav aria-label="Navegação principal" className="flex items-center gap-1">
          {NAV_TABS.map((tab) => {
            const isActive = tab.id === activeTab
            return (
              <Link
                key={tab.id}
                to={tab.href}
                aria-current={isActive ? 'page' : undefined}
                className={[
                  'px-3 py-1 text-sm rounded-sm transition-colors',
                  isActive
                    ? 'text-[#0D6EFD] border-b-2 border-[#0D6EFD] font-medium'
                    : 'text-[#475569] hover:text-[#0D6EFD]',
                ].join(' ')}
              >
                {tab.label}
              </Link>
            )
          })}
        </nav>
      </div>

      {/* Right: User + Logout */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-[#475569]">
          👤 {user?.name ?? 'Utilizador'}
        </span>
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          Sair
        </Button>
      </div>
    </header>
  )
}
