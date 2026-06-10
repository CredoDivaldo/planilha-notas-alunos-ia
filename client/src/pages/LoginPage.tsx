import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { GraduationCap, Mail, Hash, Lock, Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type Tab = 'professor' | 'estudante'

function PasswordRequirement({ met, label }: { met: boolean; label: string }) {
  return (
    <p className="text-sm flex items-center gap-1.5">
      {met ? (
        <CheckCircle className="size-4 text-success shrink-0" />
      ) : (
        <XCircle className="size-4 text-muted-foreground shrink-0" />
      )}
      <span className={met ? 'text-success' : 'text-muted-foreground'}>{label}</span>
    </p>
  )
}

export default function LoginPage() {
  const { login, isAuthenticated, role: currentRole, changePassword, requiresPasswordChange } =
    useAuth()
  const navigate = useNavigate()

  const [tab, setTab] = useState<Tab>('professor')
  const [email, setEmail] = useState('')
  const [studentNumber, setStudentNumber] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [changeLoading, setChangeLoading] = useState(false)
  const [changeError, setChangeError] = useState('')

  if (isAuthenticated && !requiresPasswordChange && currentRole) {
    const dest =
      currentRole === 'professor' ? '/painel' :
      currentRole === 'estudante' ? '/portal' : '/delegado'
    navigate(dest, { replace: true })
    return null
  }

  const identifier = tab === 'professor' ? email : studentNumber
  const canSubmit = identifier.trim().length > 0 && password.trim().length > 0 && !loading

  const handleTabChange = (t: Tab) => {
    setTab(t)
    setError('')
    const params = new URLSearchParams(window.location.search)
    params.set('role', t)
    window.history.replaceState({}, '', `${window.location.pathname}?${params}`)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login({ email_or_student_number: identifier, password, role: tab })
    } catch (err: unknown) {
      if (err instanceof Error) {
        const msg = err.message
        if (msg.includes('401') || msg.toLowerCase().includes('login failed')) {
          setError('Email ou palavra-passe incorrectos.')
        } else if (msg.includes('403')) {
          setError('Conta suspensa. Contacte o administrador.')
        } else {
          setError('Erro ao iniciar sessão. Tente novamente.')
        }
      }
    } finally {
      setLoading(false)
    }
  }

  const hasMinLength = newPassword.length >= 8
  const hasUppercase = /[A-Z]/.test(newPassword)
  const passwordsMatch = newPassword === confirmPassword && newPassword.length > 0
  const canChangePassword = hasMinLength && hasUppercase && passwordsMatch && !changeLoading

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setChangeError('')
    setChangeLoading(true)
    try {
      await changePassword({ new_password: newPassword, confirm_password: confirmPassword })
      if (currentRole) {
        const dest =
          currentRole === 'professor' ? '/painel' :
          currentRole === 'estudante' ? '/portal' : '/delegado'
        navigate(dest, { replace: true })
      }
    } catch (err: unknown) {
      setChangeError(err instanceof Error ? err.message : 'Erro ao alterar palavra-passe.')
    } finally {
      setChangeLoading(false)
    }
  }

  /* ── First access — change password ─────────────────────────────────────── */
  if (requiresPasswordChange) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-gradient">
        <div className="w-full max-w-[440px] glass rounded-2xl p-8">
          <div className="flex items-center gap-3 mb-6">
            <Lock className="size-6 text-primary" />
            <h1 className="text-xl font-semibold text-foreground">Primeiro Acesso</h1>
          </div>
          <p className="text-sm text-muted-foreground mb-6">
            Defina uma palavra-passe segura para a sua conta.
          </p>
          <form onSubmit={handleChangePassword} className="flex flex-col gap-4" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="new-password">Nova palavra-passe</Label>
              <div className="relative">
                <Input
                  id="new-password"
                  type={showNew ? 'text' : 'password'}
                  value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  autoFocus
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowNew(!showNew)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  tabIndex={-1}
                >
                  {showNew ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirm-password">Confirmar palavra-passe</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50">
              <PasswordRequirement met={hasMinLength} label="mínimo 8 caracteres" />
              <PasswordRequirement met={hasUppercase} label="pelo menos uma letra maiúscula" />
              <PasswordRequirement met={passwordsMatch} label="palavras-passe coincidem" />
            </div>
            {changeError && (
              <p role="alert" className="text-sm text-destructive">{changeError}</p>
            )}
            <Button type="submit" disabled={!canChangePassword} className="w-full">
              {changeLoading ? 'A definir…' : 'Definir e Entrar'}
            </Button>
          </form>
        </div>
      </div>
    )
  }

  /* ── Login ───────────────────────────────────────────────────────────────── */
  return (
    <div className="min-h-screen flex bg-dark-gradient">

      {/* Left panel — brand */}
      <div className="hidden lg:flex w-1/2 relative overflow-hidden flex-col justify-center px-16"
        style={{ background: 'linear-gradient(160deg, #1e3a8a, #2563eb)' }}
      >
        {/* Decorative circles */}
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full"
          style={{ background: 'rgba(255,255,255,0.08)' }} />
        <div className="absolute -bottom-20 -left-20 w-60 h-60 rounded-full"
          style={{ background: 'rgba(255,255,255,0.05)' }} />

        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-8">
            <GraduationCap className="size-12 text-white" />
            <span className="text-4xl font-bold text-white">UniGrade</span>
          </div>
          <h2 className="text-3xl font-semibold text-white leading-snug mb-4">
            Sistema Inteligente de<br />Gestão Académica
          </h2>
          <p className="text-blue-200 text-lg leading-relaxed">
            Universidade Lusíada de Angola.<br />
            Gerencie notas, notifique estudantes<br />e acompanhe o desempenho académico.
          </p>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-8 py-12">
        <div className="w-full max-w-[380px]">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <GraduationCap className="size-8 text-primary" />
            <span className="text-2xl font-bold text-foreground">UniGrade</span>
          </div>

          <h2 className="text-3xl font-bold text-foreground mb-2">Bem-vindo</h2>
          <p className="text-muted-foreground mb-8">Entre na sua conta para continuar</p>

          {/* Tab selector */}
          <div
            className="flex mb-6 border-b border-border"
            role="tablist"
            aria-label="Tipo de utilizador"
          >
            {(['professor', 'estudante'] as Tab[]).map(t => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                onClick={() => handleTabChange(t)}
                className={`px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-ring ${
                  tab === t
                    ? 'border-b-2 border-primary text-primary'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {t === 'professor' ? 'Professor' : 'Estudante'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
            {tab === 'professor' ? (
              <div className="space-y-1.5">
                <Label htmlFor="email">Email institucional</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="email@unila.ao"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    className="pl-10"
                    autoComplete="username"
                    autoFocus
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-1.5">
                <Label htmlFor="student-number">Número de Estudante</Label>
                <div className="relative">
                  <Hash className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                  <Input
                    id="student-number"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]*"
                    placeholder="ex: 2023001"
                    value={studentNumber}
                    onChange={e => setStudentNumber(e.target.value)}
                    className="pl-10"
                    autoFocus
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="password">Palavra-passe</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="pl-10 pr-10"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div role="alert" className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
                <XCircle className="size-4 shrink-0" />
                {error}
              </div>
            )}

            <Button type="submit" disabled={!canSubmit} className="w-full glow-blue">
              {loading ? 'A entrar…' : tab === 'professor' ? 'Entrar' : 'Entrar como Aluno'}
            </Button>
          </form>

          {tab === 'professor' && (
            <p className="mt-6 text-center text-sm text-muted-foreground">
              Ainda não tem conta?{' '}
              <Link to="/register" className="text-primary hover:underline font-medium">
                Criar conta de professor
              </Link>
            </p>
          )}

          {tab === 'estudante' && (
            <p className="mt-4 text-xs text-muted-foreground text-center">
              Primeiro acesso? Será pedida troca de palavra-passe.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
