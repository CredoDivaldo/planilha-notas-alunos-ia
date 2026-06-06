import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { FormField } from '@/components/molecules/FormField'

type Tab = 'professor' | 'estudante'

function Spinner() {
  return (
    <svg
      className="mr-2 h-4 w-4 animate-spin"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  )
}

function PasswordRequirement({ met, label }: { met: boolean; label: string }) {
  return (
    <p
      className="text-sm flex items-center gap-1.5"
      aria-label={`${label}: ${met ? 'satisfeito' : 'não satisfeito'}`}
    >
      <span aria-hidden="true">{met ? '✅' : '❌'}</span>
      <span className={met ? 'text-[#15803D]' : 'text-[#475569]'}>{label}</span>
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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [changeLoading, setChangeLoading] = useState(false)
  const [changeError, setChangeError] = useState('')

  // AC15: already authenticated and no pending password change → redirect
  if (isAuthenticated && !requiresPasswordChange && currentRole) {
    const dest =
      currentRole === 'professor'
        ? '/painel'
        : currentRole === 'estudante'
          ? '/portal'
          : '/delegado'
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
      await login({
        email_or_student_number: identifier,
        password,
        role: tab,
      })
      // Redirect handled by the guard above on re-render (if not requiresPasswordChange)
    } catch (err: unknown) {
      if (err instanceof Error) {
        const msg = err.message
        if (msg.includes('401') || msg.toLowerCase().includes('login failed')) {
          setError('⚠️ Email ou palavra-passe incorrectos.')
        } else if (msg.includes('403')) {
          setError('❌ Conta suspensa. Contacte o administrador.')
        } else {
          setError('⚠️ Erro ao iniciar sessão. Tente novamente.')
        }
      }
    } finally {
      setLoading(false)
    }
  }

  // Password requirements
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
      // After successful change, redirect based on role
      if (currentRole) {
        const dest =
          currentRole === 'professor'
            ? '/painel'
            : currentRole === 'estudante'
              ? '/portal'
              : '/delegado'
        navigate(dest, { replace: true })
      }
    } catch (err: unknown) {
      setChangeError(
        err instanceof Error ? err.message : 'Erro ao alterar palavra-passe.',
      )
    } finally {
      setChangeLoading(false)
    }
  }

  // AC10–AC13: First access form
  if (requiresPasswordChange) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <div className="w-full max-w-[440px] rounded-xl border bg-white p-8 shadow-sm">
          <h1 className="text-xl font-semibold mb-6">🔐 Primeiro Acesso</h1>
          <form onSubmit={handleChangePassword} className="flex flex-col gap-4" noValidate>
            <FormField
              id="new-password"
              label="Nova palavra-passe"
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              autoFocus
            />
            <FormField
              id="confirm-password"
              label="Confirmar palavra-passe"
              type="password"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              error={
                confirmPassword.length > 0 && !passwordsMatch
                  ? 'As palavras-passe não coincidem.'
                  : undefined
              }
            />
            <div className="flex flex-col gap-1 p-3 rounded-lg bg-[#F8FAFC]">
              <PasswordRequirement met={hasMinLength} label="mín. 8 caracteres" />
              <PasswordRequirement met={hasUppercase} label="letra maiúscula" />
            </div>
            {changeError && (
              <p role="alert" aria-live="assertive" className="text-sm text-[#B91C1C]">
                {changeError}
              </p>
            )}
            <Button
              type="submit"
              disabled={!canChangePassword}
              className="w-full bg-[#0D6EFD] hover:bg-[#0b5ed7] disabled:opacity-50"
            >
              {changeLoading ? (
                <>
                  <Spinner />
                  A definir…
                </>
              ) : (
                'Definir e Entrar'
              )}
            </Button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
      <div className="w-full max-w-[440px] rounded-xl border bg-white p-8 shadow-sm">
        {/* Header — AC1 */}
        <h1 className="text-xl font-semibold mb-6">📊 Planilha Notas</h1>

        {/* Tabs — AC2 */}
        <div
          className="flex mb-6 border-b border-gray-200"
          role="tablist"
          aria-label="Tipo de utilizador"
        >
          {(['professor', 'estudante'] as Tab[]).map(t => (
            <button
              key={t}
              role="tab"
              aria-selected={tab === t}
              onClick={() => handleTabChange(t)}
              className={`px-4 py-2 text-sm font-medium capitalize transition-colors focus-visible:outline-2 focus-visible:outline-[#0D6EFD] ${
                tab === t
                  ? 'border-b-2 border-[#0D6EFD] text-[#0D6EFD]'
                  : 'text-[#475569] hover:text-gray-900'
              }`}
            >
              {t === 'professor' ? 'Professor' : 'Estudante'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
          {/* AC3 — Professor fields */}
          {tab === 'professor' && (
            <FormField
              id="email"
              label="Email / Utilizador"
              type="email"
              placeholder="email@inst.ao"
              value={email}
              onChange={e => setEmail(e.target.value)}
              autoComplete="username"
              autoFocus
            />
          )}

          {/* AC4 — Estudante fields */}
          {tab === 'estudante' && (
            <FormField
              id="student-number"
              label="Número de Estudante"
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              placeholder="ex: 2023001"
              value={studentNumber}
              onChange={e => setStudentNumber(e.target.value)}
              autoFocus
            />
          )}

          <FormField
            id="password"
            label="Palavra-passe"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            autoComplete="current-password"
          />

          {/* AC7 + AC8 errors */}
          {error && (
            <p role="alert" aria-live="assertive" className="text-sm text-[#B91C1C]">
              {error}
            </p>
          )}

          <Button
            type="submit"
            disabled={!canSubmit}
            className="w-full bg-[#0D6EFD] hover:bg-[#0b5ed7] disabled:opacity-50"
          >
            {loading ? (
              <>
                <Spinner /> A entrar…
              </>
            ) : tab === 'professor' ? (
              'Entrar'
            ) : (
              'Entrar como Aluno'
            )}
          </Button>
        </form>

        {tab === 'estudante' && (
          <p className="mt-4 text-xs text-[#475569]">
            ⚠️ Primeiro acesso? Será pedida troca de palavra-passe.
          </p>
        )}
      </div>
    </div>
  )
}
