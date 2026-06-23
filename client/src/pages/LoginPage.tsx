import { useState, useEffect } from 'react'
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

// Página de login. Exemplo típico de componente React com "estado": cada `useState`
// cria uma variável que, quando muda, faz a página voltar a desenhar-se. Aqui há
// estado para o separador activo, email, senha, erros, etc.
export default function LoginPage() {
  // useAuth() dá acesso às funções de autenticação partilhadas (ver AuthContext).
  const { login, isAuthenticated, role: currentRole, changePassword, requiresPasswordChange,
    checkStudentStatus, activateStudent } = useAuth()
  const navigate = useNavigate()  // permite mudar de página por código

  // [valor, função-que-o-altera] = useState(valorInicial)
  const [tab, setTab] = useState<Tab>('professor')
  const [email, setEmail] = useState('')
  const [studentNumber, setStudentNumber] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  // Student two-step flow: enter number → verify → log in or set first password
  const [studentStep, setStudentStep] = useState<'number' | 'login' | 'register'>('number')
  const [checkingStudent, setCheckingStudent] = useState(false)
  const [studentConfirmPw, setStudentConfirmPw] = useState('')

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [changeLoading, setChangeLoading] = useState(false)
  const [changeError, setChangeError] = useState('')

  // useEffect: corre quando algo na lista de dependências (no fim) muda. Aqui,
  // assim que o utilizador fica autenticado, reencaminha-o para o painel certo.
  useEffect(() => {
    if (isAuthenticated && !requiresPasswordChange && currentRole) {
      const dest =
        currentRole === 'professor' ? '/painel' :
        currentRole === 'estudante' ? '/portal' : '/delegado'
      navigate(dest, { replace: true })
    }
  }, [isAuthenticated, requiresPasswordChange, currentRole, navigate])

  if (isAuthenticated && !requiresPasswordChange && currentRole) return null

  // Student password requirements (first access)
  const stuHasMinLen = password.length >= 8
  const stuHasUpper = /[A-Z]/.test(password)
  const stuPwMatch = password.length > 0 && password === studentConfirmPw

  const canSubmit =
    tab === 'professor'
      ? email.trim().length > 0 && password.trim().length > 0 && !loading
      : studentStep === 'number'
        ? studentNumber.trim().length > 0 && !checkingStudent
        : studentStep === 'login'
          ? password.trim().length > 0 && !loading
          : stuHasMinLen && stuHasUpper && stuPwMatch && !loading // register

  const handleTabChange = (t: Tab) => {
    setTab(t)
    setError('')
    setStudentStep('number')
    setPassword('')
    setStudentConfirmPw('')
    const params = new URLSearchParams(window.location.search)
    params.set('role', t)
    window.history.replaceState({}, '', `${window.location.pathname}?${params}`)
  }

  // Reset to step 1 if the student edits the number after verifying
  const handleStudentNumberChange = (value: string) => {
    setStudentNumber(value)
    if (studentStep !== 'number') {
      setStudentStep('number')
      setPassword('')
      setStudentConfirmPw('')
      setError('')
    }
  }

  const verifyStudentNumber = async () => {
    setError('')
    const num = studentNumber.trim()
    if (!num) return
    setCheckingStudent(true)
    try {
      const status = await checkStudentStatus(num)
      if (!status.found_in_roster) {
        setError('Número de estudante não reconhecido. Fala com o teu professor.')
        return
      }
      setStudentStep(status.has_account ? 'login' : 'register')
    } catch {
      setError('Erro ao verificar o número. Tenta novamente.')
    } finally {
      setCheckingStudent(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (tab === 'professor') {
      setLoading(true)
      try {
        await login({ email_or_student_number: email, password, role: 'professor' })
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : ''
        if (msg.includes('401') || msg.toLowerCase().includes('login failed')) setError('Email ou palavra-passe incorrectos.')
        else if (msg.includes('403')) setError('Conta suspensa. Contacte o administrador.')
        else setError(msg || 'Erro ao iniciar sessão. Tente novamente.')
      } finally {
        setLoading(false)
      }
      return
    }

    // Student flow
    if (studentStep === 'number') {
      await verifyStudentNumber()
      return
    }
    setLoading(true)
    try {
      if (studentStep === 'login') {
        await login({ email_or_student_number: studentNumber.trim(), password, role: 'estudante' })
      } else {
        // register (first access)
        if (!stuPwMatch) { setError('As palavras-passe não coincidem.'); return }
        if (!stuHasMinLen || !stuHasUpper) { setError('A palavra-passe deve ter pelo menos 8 caracteres e uma maiúscula.'); return }
        await activateStudent(studentNumber.trim(), password)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : ''
      if (msg.includes('401') || msg.toLowerCase().includes('login failed')) setError('Palavra-passe incorrecta.')
      else if (msg.includes('403')) setError('Conta suspensa. Contacte o administrador.')
      else setError(msg || 'Erro ao iniciar sessão. Tente novamente.')
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
                    onChange={e => handleStudentNumberChange(e.target.value)}
                    className="pl-10"
                    autoFocus
                    readOnly={studentStep !== 'number'}
                  />
                </div>
                {studentStep === 'register' && (
                  <p className="text-xs text-success">
                    Primeiro acesso — define a tua palavra-passe.
                  </p>
                )}
              </div>
            )}

            {/* Password field: always for professor; for student only after the number is verified */}
            {(tab === 'professor' || studentStep !== 'number') && (
              <div className="space-y-1.5">
                <Label htmlFor="password">
                  {studentStep === 'register' ? 'Criar palavra-passe' : 'Palavra-passe'}
                </Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    className="pl-10 pr-10"
                    autoComplete={studentStep === 'register' ? 'new-password' : 'current-password'}
                    autoFocus={tab === 'estudante'}
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
            )}

            {/* Confirm + requirements: only on student first access */}
            {tab === 'estudante' && studentStep === 'register' && (
              <div className="space-y-1.5">
                <Label htmlFor="student-confirm">Confirmar palavra-passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                  <Input
                    id="student-confirm"
                    type={showPassword ? 'text' : 'password'}
                    value={studentConfirmPw}
                    onChange={e => setStudentConfirmPw(e.target.value)}
                    className="pl-10"
                    autoComplete="new-password"
                  />
                </div>
                <div className="space-y-1 pt-1">
                  <PasswordRequirement met={stuHasMinLen} label="Pelo menos 8 caracteres" />
                  <PasswordRequirement met={stuHasUpper} label="Pelo menos uma letra maiúscula" />
                  <PasswordRequirement met={stuPwMatch} label="As palavras-passe coincidem" />
                </div>
              </div>
            )}

            {error && (
              <div role="alert" className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
                <XCircle className="size-4 shrink-0" />
                {error}
              </div>
            )}

            <Button type="submit" disabled={!canSubmit} className="w-full glow-blue">
              {tab === 'professor'
                ? (loading ? 'A entrar…' : 'Entrar')
                : studentStep === 'number'
                  ? (checkingStudent ? 'A verificar…' : 'Continuar')
                  : studentStep === 'register'
                    ? (loading ? 'A criar…' : 'Criar palavra-passe e entrar')
                    : (loading ? 'A entrar…' : 'Entrar')}
            </Button>

            {tab === 'estudante' && studentStep !== 'number' && (
              <button
                type="button"
                onClick={() => handleStudentNumberChange(studentNumber)}
                className="text-xs text-muted-foreground hover:text-foreground text-center"
              >
                ← Usar outro número
              </button>
            )}
          </form>

          {tab === 'professor' && (
            <p className="mt-6 text-center text-sm text-muted-foreground">
              Ainda não tem conta?{' '}
              <Link to="/register" className="text-primary hover:underline font-medium">
                Criar conta de professor
              </Link>
            </p>
          )}

          {tab === 'estudante' && studentStep === 'number' && (
            <p className="mt-4 text-xs text-muted-foreground text-center">
              Insere o teu número de estudante para continuar.
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
