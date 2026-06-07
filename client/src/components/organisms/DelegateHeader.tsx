import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'

interface DelegateHeaderProps {
  turma?: string
  semester?: string
}

export function DelegateHeader({
  turma = 'ING-T1',
  semester = '2026/1',
}: DelegateHeaderProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="bg-white border-b border-slate-200 px-6 h-14 flex items-center justify-between">
      {/* Left: Logo + Badge + Turma */}
      <div className="flex items-center gap-4">
        <span className="font-semibold text-[#0D6EFD] text-base select-none">
          📊 Planilha Notas
        </span>

        <span
          role="status"
          aria-label="Modo de acesso: Delegado de turma, apenas leitura"
          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold text-white select-none"
          style={{ backgroundColor: '#B45309' }}
        >
          MODO DELEGADO
        </span>

        <span className="text-sm text-[#475569]">
          Turma: <strong>{turma}</strong>&nbsp;&nbsp;Sem. {semester}
        </span>
      </div>

      {/* Right: User + Logout */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-[#475569]">
          👤 {user?.name ?? 'Delegado'}
        </span>
        <Button variant="ghost" size="sm" onClick={handleLogout}>
          Sair
        </Button>
      </div>
    </header>
  )
}
