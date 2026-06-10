import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  GraduationCap, User, Mail, Lock, Eye, EyeOff, Building, BookOpen,
  CheckCircle, ArrowRight, ArrowLeft, Plus, X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'

const STEPS = ['Dados Pessoais', 'Credenciais', 'Instituição']
const INSTITUTION_DEFAULT = 'Universidade Lusíada de Angola'

const COMMON_DISCIPLINES = [
  'Matemática', 'Física', 'Química', 'Inglês Técnico', 'Programação',
  'Estrutura de Dados', 'Cálculo', 'Álgebra Linear', 'Estatística',
  'Sistemas Operativos', 'Redes', 'Base de Dados', 'Gestão',
]

interface FormState {
  fullName: string
  email: string
  password: string
  confirmPassword: string
  institution: string
  faculty: string
  disciplines: string[]
}

const INITIAL: FormState = {
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  institution: INSTITUTION_DEFAULT,
  faculty: '',
  disciplines: [],
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const [step, setStep] = useState(0)
  const [form, setForm] = useState<FormState>(INITIAL)
  const [disciplineInput, setDisciplineInput] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const set = (field: keyof FormState, value: string) =>
    setForm(prev => ({ ...prev, [field]: value }))

  const hasMinLength = form.password.length >= 8
  const hasUppercase = /[A-Z]/.test(form.password)
  const passwordsMatch = form.password === form.confirmPassword && form.password.length > 0

  const canStep0 = form.fullName.trim().length >= 2 && /\S+@\S+\.\S+/.test(form.email)
  const canStep1 = hasMinLength && hasUppercase && passwordsMatch
  const canStep2 = form.institution.trim().length > 0

  const addDiscipline = (name: string) => {
    const trimmed = name.trim()
    if (!trimmed || form.disciplines.includes(trimmed)) return
    setForm(prev => ({ ...prev, disciplines: [...prev.disciplines, trimmed] }))
    setDisciplineInput('')
  }

  const removeDiscipline = (name: string) =>
    setForm(prev => ({ ...prev, disciplines: prev.disciplines.filter(d => d !== name) }))

  const handleSubmit = async () => {
    setError('')
    setLoading(true)
    try {
      const base = import.meta.env.VITE_API_BASE_URL ?? ''
      const res = await fetch(`${base}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: form.fullName,
          email: form.email,
          password: form.password,
          institution: form.institution,
          faculty: form.faculty,
          disciplines: form.disciplines,
        }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: 'Erro ao criar conta.' })) as { detail?: string }
        throw new Error(body.detail ?? `Erro ${res.status}`)
      }
      navigate('/login?registered=1', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao criar conta.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-dark-gradient">

      {/* Left panel */}
      <div className="hidden lg:flex w-2/5 relative overflow-hidden flex-col justify-center px-14"
        style={{ background: 'linear-gradient(160deg, #1e3a8a, #2563eb)' }}
      >
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full"
          style={{ background: 'rgba(255,255,255,0.08)' }} />
        <div className="absolute -bottom-20 -left-20 w-60 h-60 rounded-full"
          style={{ background: 'rgba(255,255,255,0.05)' }} />
        <div className="relative z-10">
          <div className="flex items-center gap-4 mb-8">
            <GraduationCap className="size-11 text-white" />
            <span className="text-3xl font-bold text-white">UniGrade</span>
          </div>
          <h2 className="text-2xl font-semibold text-white leading-snug mb-4">
            Crie a sua conta de professor
          </h2>
          <p className="text-blue-200 leading-relaxed">
            Universidade Lusíada de Angola.<br />
            Em apenas 3 passos, terá acesso a todas as funcionalidades de gestão académica.
          </p>

          {/* Step indicators */}
          <div className="mt-10 flex flex-col gap-3">
            {STEPS.map((label, i) => (
              <div key={i} className={`flex items-center gap-3 text-sm ${i === step ? 'text-white font-semibold' : i < step ? 'text-blue-300' : 'text-blue-400/60'}`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  i < step ? 'bg-white/30' : i === step ? 'bg-white text-blue-700' : 'bg-white/10'
                }`}>
                  {i < step ? <CheckCircle className="size-4" /> : i + 1}
                </div>
                {label}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-8 py-12">
        <div className="w-full max-w-[400px]">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <GraduationCap className="size-7 text-primary" />
            <span className="text-xl font-bold text-foreground">UniGrade</span>
          </div>

          {/* Step header */}
          <div className="mb-2 text-xs font-semibold text-primary uppercase tracking-widest">
            Passo {step + 1} de {STEPS.length}
          </div>
          <h2 className="text-2xl font-bold text-foreground mb-1">{STEPS[step]}</h2>
          <div className="w-full h-1 bg-border rounded-full mb-8">
            <div
              className="h-1 bg-primary rounded-full transition-all duration-500"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>

          {/* ── Step 0: Dados Pessoais ──────────────────────────────────── */}
          {step === 0 && (
            <div className="flex flex-col gap-5">
              <div className="space-y-1.5">
                <Label htmlFor="fullName">Nome completo</Label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                  <Input
                    id="fullName"
                    type="text"
                    placeholder="Dr. João Silva"
                    value={form.fullName}
                    onChange={e => set('fullName', e.target.value)}
                    className="pl-10"
                    autoFocus
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="email">Email institucional</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="joao.silva@unila.ao"
                    value={form.email}
                    onChange={e => set('email', e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <Button
                onClick={() => setStep(1)}
                disabled={!canStep0}
                className="w-full gap-2"
              >
                Continuar <ArrowRight className="size-4" />
              </Button>
            </div>
          )}

          {/* ── Step 1: Credenciais ─────────────────────────────────────── */}
          {step === 1 && (
            <div className="flex flex-col gap-5">
              <div className="space-y-1.5">
                <Label htmlFor="password">Palavra-passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={form.password}
                    onChange={e => set('password', e.target.value)}
                    className="pl-10 pr-10"
                    autoFocus
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
              <div className="space-y-1.5">
                <Label htmlFor="confirm">Confirmar palavra-passe</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                  <Input
                    id="confirm"
                    type="password"
                    value={form.confirmPassword}
                    onChange={e => set('confirmPassword', e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1.5 p-3 rounded-lg bg-muted/50 text-sm">
                {[
                  { met: hasMinLength, label: 'mínimo 8 caracteres' },
                  { met: hasUppercase, label: 'letra maiúscula' },
                  { met: passwordsMatch, label: 'palavras-passe coincidem' },
                ].map(({ met, label }) => (
                  <div key={label} className={`flex items-center gap-2 ${met ? 'text-success' : 'text-muted-foreground'}`}>
                    <CheckCircle className={`size-4 ${met ? 'opacity-100' : 'opacity-30'}`} />
                    {label}
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(0)} className="gap-1.5">
                  <ArrowLeft className="size-4" /> Voltar
                </Button>
                <Button onClick={() => setStep(2)} disabled={!canStep1} className="flex-1 gap-2">
                  Continuar <ArrowRight className="size-4" />
                </Button>
              </div>
            </div>
          )}

          {/* ── Step 2: Instituição ─────────────────────────────────────── */}
          {step === 2 && (
            <div className="flex flex-col gap-5">
              <div className="space-y-1.5">
                <Label htmlFor="institution">Instituição</Label>
                <div className="relative">
                  <Building className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                  <Input
                    id="institution"
                    value={form.institution}
                    onChange={e => set('institution', e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="faculty">Faculdade / Departamento <span className="text-muted-foreground">(opcional)</span></Label>
                <Input
                  id="faculty"
                  placeholder="ex: Engenharia Informática"
                  value={form.faculty}
                  onChange={e => set('faculty', e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Disciplinas que lecciona <span className="text-muted-foreground">(opcional)</span></Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <BookOpen className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-primary" />
                    <Input
                      placeholder="Adicionar disciplina…"
                      value={disciplineInput}
                      onChange={e => setDisciplineInput(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter') { e.preventDefault(); addDiscipline(disciplineInput) }
                      }}
                      className="pl-10"
                    />
                  </div>
                  <Button variant="outline" size="icon" onClick={() => addDiscipline(disciplineInput)}>
                    <Plus className="size-4" />
                  </Button>
                </div>
                {/* Quick add suggestions */}
                <div className="flex flex-wrap gap-1.5">
                  {COMMON_DISCIPLINES.filter(d => !form.disciplines.includes(d)).slice(0, 6).map(d => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => addDiscipline(d)}
                      className="text-xs px-2 py-1 rounded-md border border-border text-muted-foreground hover:text-foreground hover:border-primary transition-colors"
                    >
                      + {d}
                    </button>
                  ))}
                </div>
                {form.disciplines.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {form.disciplines.map(d => (
                      <Badge key={d} variant="secondary" className="gap-1.5">
                        {d}
                        <button type="button" onClick={() => removeDiscipline(d)}>
                          <X className="size-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              {error && (
                <div role="alert" className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-lg px-3 py-2">
                  {error}
                </div>
              )}

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setStep(1)} className="gap-1.5">
                  <ArrowLeft className="size-4" /> Voltar
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={!canStep2 || loading}
                  className="flex-1 gap-2 glow-blue"
                >
                  {loading ? 'A criar conta…' : (
                    <><CheckCircle className="size-4" /> Criar Conta</>
                  )}
                </Button>
              </div>
            </div>
          )}

          <p className="mt-8 text-center text-sm text-muted-foreground">
            Já tem conta?{' '}
            <Link to="/login" className="text-primary hover:underline font-medium">
              Iniciar sessão
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
