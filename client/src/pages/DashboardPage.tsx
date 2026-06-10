import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'

export default function DashboardPage() {
  const { isAuthenticated, role } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { replace: true })
      return
    }
    if (role === 'professor') navigate('/painel', { replace: true })
    else if (role === 'estudante') navigate('/portal', { replace: true })
    else if (role === 'delegado') navigate('/delegado', { replace: true })
    else navigate('/login', { replace: true })
  }, [isAuthenticated, role, navigate])

  return null
}
