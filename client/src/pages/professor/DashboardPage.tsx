import { useEffect, useReducer, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppHeader } from '@/components/organisms/AppHeader'
import { ContextBar } from '@/components/molecules/ContextBar'
import { FileDropzone } from '@/components/molecules/FileDropzone'
import { StepCard } from '@/components/organisms/StepCard'
import type { StepStatus } from '@/components/organisms/StepCard'
import { ProgressStepper } from '@/components/organisms/ProgressStepper'
import { QuickStatsSidebar } from '@/components/organisms/QuickStatsSidebar'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'

// ─── State types ─────────────────────────────────────────────────────────────

interface StepState {
  status: StepStatus
  data?: Record<string, unknown>
}

type PanelState = [StepState, StepState, StepState, StepState, StepState]

interface QuickStats {
  estudantes: number
  notas: number
  matched: number
  semMatch: number
  telInvalido: number
  enviados: number
  falhas: number
}

// ─── State helpers ────────────────────────────────────────────────────────────

const INITIAL_STATE: PanelState = [
  { status: 'active' },
  { status: 'locked' },
  { status: 'locked' },
  { status: 'locked' },
  { status: 'locked' },
]

const INITIAL_STATS: QuickStats = {
  estudantes: 0,
  notas: 0,
  matched: 0,
  semMatch: 0,
  telInvalido: 0,
  enviados: 0,
  falhas: 0,
}

function completeStep(state: PanelState, i: number, data?: Record<string, unknown>): PanelState {
  const next = state.map((s) => ({ ...s })) as PanelState
  next[i] = { status: 'completed', data: data ?? next[i].data }
  if (i + 1 < 5) {
    next[i + 1] = { ...next[i + 1], status: 'active' }
  }
  return next
}

function errorStep(state: PanelState, i: number): PanelState {
  const next = state.map((s) => ({ ...s })) as PanelState
  next[i] = { ...next[i], status: 'error' }
  return next
}

function loadState(): PanelState {
  try {
    const raw = sessionStorage.getItem('painel_step_states')
    return raw ? (JSON.parse(raw) as PanelState) : INITIAL_STATE
  } catch {
    return INITIAL_STATE
  }
}

function saveState(state: PanelState) {
  sessionStorage.setItem('painel_step_states', JSON.stringify(state))
}

// ─── Match result shape (Story 8.2 — backed by /api/v1/grades/match) ─────────

interface MatchResult {
  student_number: string
  name: string
  grade: number | null
  status: 'matched' | 'no_grade' | 'no_phone'
}

interface MatchResponse {
  matched: number
  unmatched: number
  invalid_phones: number
  items: Array<{
    numero_estudante: string
    nome: string
    turma: string
    whatsapp: string
    nota: string
  }>
}

function deriveStatus(item: MatchResponse['items'][number]): MatchResult['status'] {
  if (!item.nota) return 'no_grade'
  if (!item.whatsapp) return 'no_phone'
  return 'matched'
}

// ─── Step reducer ─────────────────────────────────────────────────────────────

type Action =
  | { type: 'COMPLETE'; index: number; data?: Record<string, unknown> }
  | { type: 'ERROR'; index: number }
  | { type: 'RESET' }

function stepReducer(state: PanelState, action: Action): PanelState {
  let next: PanelState
  switch (action.type) {
    case 'COMPLETE':
      next = completeStep(state, action.index, action.data)
      break
    case 'ERROR':
      next = errorStep(state, action.index)
      break
    case 'RESET':
      next = [...INITIAL_STATE] as PanelState
      break
    default:
      return state
  }
  saveState(next)
  return next
}

// ─── Token helper for FormData uploads ───────────────────────────────────────

function getAuthToken(): string | null {
  try {
    const stored = localStorage.getItem('auth_user')
    return stored ? (JSON.parse(stored) as { token: string }).token : null
  } catch {
    return null
  }
}

function getApiBase(): string {
  return (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'
}

// ─── Status badge helper ──────────────────────────────────────────────────────

function MatchStatusBadge({ status }: { status: MatchResult['status'] }) {
  if (status === 'matched') return <span className="text-[#15803D] font-medium">✅ Match</span>
  if (status === 'no_grade') return <span className="text-[#B91C1C] font-medium">❌ Sem nota</span>
  return <span className="text-[#B45309] font-medium">⚠️ Sem telefone</span>
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function ProfessorDashboardPage() {
  const navigate = useNavigate()

  // Step state
  const [steps, dispatch] = useReducer(stepReducer, undefined, loadState)

  // Quick stats
  const [stats, setStats] = useState<QuickStats>(INITIAL_STATS)

  // Step 1 — Upload Estudantes
  const [step1Loading, setStep1Loading] = useState(false)
  const [step1Error, setStep1Error] = useState<string | undefined>()

  // Step 2 — Upload Notas
  const [step2Loading, setStep2Loading] = useState(false)
  const [step2Error, setStep2Error] = useState<string | undefined>()

  // Step 3 — Match
  const [step3Loading, setStep3Loading] = useState(false)
  const [step3Error, setStep3Error] = useState<string | undefined>()
  const [matchResults, setMatchResults] = useState<MatchResult[]>([])
  const [matchTimestamp, setMatchTimestamp] = useState<string | null>(null)
  const [matchDialogOpen, setMatchDialogOpen] = useState(false)

  // Step 4 — QR WhatsApp
  const [countdown, setCountdown] = useState(45)
  const [qrExpired, setQrExpired] = useState(false)
  const [qrConnected, setQrConnected] = useState(false)
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const autoConnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Step 5 — Disparar
  const [broadcastMode, setBroadcastMode] = useState<'simulation' | 'real'>('simulation')
  const [broadcastMessage, setBroadcastMessage] = useState(
    'Olá {nome}! A sua nota de {disciplina} é {nota}. Cumprimentos.',
  )
  const [broadcastLoading, setBroadcastLoading] = useState(false)
  const [broadcastError, setBroadcastError] = useState<string | undefined>()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [confirmChecked, setConfirmChecked] = useState(false)

  // ─── QR countdown effects ───────────────────────────────────────────────

  const startCountdown = () => {
    if (countdownRef.current) clearInterval(countdownRef.current)
    if (autoConnectRef.current) clearTimeout(autoConnectRef.current)
    setCountdown(45)
    setQrExpired(false)
    setQrConnected(false)

    countdownRef.current = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(countdownRef.current!)
          setQrExpired(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    // Story 8.2: poll the real Evolution connect endpoint every 5s.
    // The endpoint returns {connected: bool}; when it flips true we mark
    // the QR card as paired and clear the countdown.
    const base = getApiBase()
    const token = getAuthToken()
    autoConnectRef.current = setTimeout(() => {
      void (async () => {
        try {
          const res = await fetch(`${base}/api/v1/whatsapp/instance/connect`, {
            method: 'GET',
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          })
          if (res.ok) {
            const data = (await res.json()) as { connected?: boolean; simulated?: boolean }
            if (data.connected) {
              setQrConnected(true)
              if (countdownRef.current) clearInterval(countdownRef.current)
            }
          }
        } catch {
          // Network errors are non-fatal — the countdown UI keeps the user
          // informed and they can refresh the QR.
        }
      })()
    }, 5000)
  }

  useEffect(() => {
    if (steps[3].status !== 'active') return
    // Defer the countdown start so setState calls happen asynchronously
    const initTimer = setTimeout(() => {
      if (!qrConnected) startCountdown()
    }, 0)
    return () => {
      clearTimeout(initTimer)
      if (countdownRef.current) clearInterval(countdownRef.current)
      if (autoConnectRef.current) clearTimeout(autoConnectRef.current)
    }
    // Only re-run when step 4 status changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [steps[3].status])

  // Auto-advance step 4 when connected
  useEffect(() => {
    if (qrConnected && steps[3].status === 'active') {
      dispatch({ type: 'COMPLETE', index: 3 })
    }
  }, [qrConnected, steps])

  // ─── Step 1 ─────────────────────────────────────────────────────────────

  const handleStudentsUpload = async (file: File) => {
    setStep1Loading(true)
    setStep1Error(undefined)
    try {
      const form = new FormData()
      form.append('file', file)
      const token = getAuthToken()
      const base = getApiBase()
      const contextId = sessionStorage.getItem('active_context_id') ?? ''
      const url = `${base}/api/v1/students/upload${contextId ? `?context_id=${contextId}` : ''}`
      const res = await fetch(url, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      })
      if (!res.ok) {
        // Surface FastAPI's sanitized detail message directly to the user
        let detail = `Upload falhou: ${res.status}`
        try {
          const body = (await res.json()) as { detail?: string }
          if (body?.detail) detail = body.detail
        } catch {
          // body wasn't JSON — keep the status-only message
        }
        throw new Error(detail)
      }
      const data = await res.json() as { count: number }
      setStats((prev) => ({ ...prev, estudantes: data.count }))
      dispatch({ type: 'COMPLETE', index: 0 })
    } catch (err) {
      setStep1Error(err instanceof Error ? err.message : 'Erro ao importar estudantes.')
      dispatch({ type: 'ERROR', index: 0 })
    } finally {
      setStep1Loading(false)
    }
  }

  // ─── Step 2 ─────────────────────────────────────────────────────────────

  const handleGradesUpload = async (file: File) => {
    setStep2Loading(true)
    setStep2Error(undefined)
    try {
      const form = new FormData()
      form.append('file', file)
      const token = getAuthToken()
      const base = getApiBase()
      const contextId = sessionStorage.getItem('active_context_id') ?? ''
      const url = `${base}/api/v1/grades/upload${contextId ? `?context_id=${contextId}` : ''}`
      const res = await fetch(url, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: form,
      })
      if (!res.ok) {
        // Surface FastAPI's sanitized detail message directly to the user
        let detail = `Upload falhou: ${res.status}`
        try {
          const body = (await res.json()) as { detail?: string }
          if (body?.detail) detail = body.detail
        } catch {
          // body wasn't JSON — keep the status-only message
        }
        throw new Error(detail)
      }
      const data = await res.json() as { count: number }
      setStats((prev) => ({ ...prev, notas: data.count }))
      dispatch({ type: 'COMPLETE', index: 1 })
    } catch (err) {
      setStep2Error(err instanceof Error ? err.message : 'Erro ao importar notas.')
      dispatch({ type: 'ERROR', index: 1 })
    } finally {
      setStep2Loading(false)
    }
  }

  // ─── Step 3 ─────────────────────────────────────────────────────────────

  const handleMatch = async () => {
    setStep3Loading(true)
    setStep3Error(undefined)
    try {
      const contextId = sessionStorage.getItem('active_context_id') ?? ''
      const body = contextId ? JSON.stringify({ context_id: contextId }) : undefined
      const base = getApiBase()
      const token = getAuthToken()
      const res = await fetch(`${base}/api/v1/grades/match`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body,
      })
      if (!res.ok) {
        let detail = `Match falhou: ${res.status}`
        try {
          const body = (await res.json()) as { detail?: string }
          if (body?.detail) detail = body.detail
        } catch {
          // body wasn't JSON — keep status-only message
        }
        throw new Error(detail)
      }
      const data = (await res.json()) as MatchResponse
      applyMatchResult(data)
    } catch (err) {
      setStep3Error(err instanceof Error ? err.message : 'Erro ao gerar match.')
      dispatch({ type: 'ERROR', index: 2 })
    } finally {
      setStep3Loading(false)
    }
  }

  function applyMatchResult(data: MatchResponse) {
    const results: MatchResult[] = data.items.map((item) => ({
      student_number: item.numero_estudante,
      name: item.nome,
      grade: item.nota ? Number(item.nota) : null,
      status: deriveStatus(item),
    }))
    setMatchResults(results)
    setMatchTimestamp(new Date().toLocaleTimeString('pt-PT'))
    setStats((prev) => ({
      ...prev,
      matched: data.matched,
      semMatch: data.unmatched,
      telInvalido: data.invalid_phones,
    }))
    dispatch({ type: 'COMPLETE', index: 2 })
  }

  // ─── Step 4 — refresh QR ─────────────────────────────────────────────────

  const handleRefreshQr = () => {
    startCountdown()
  }

  // ─── Step 5 — Broadcast ──────────────────────────────────────────────────

  const handleBroadcastClick = () => {
    if (broadcastMode === 'real') {
      setConfirmChecked(false)
      setConfirmOpen(true)
    } else {
      executeBroadcast()
    }
  }

  const executeBroadcast = async () => {
    setBroadcastLoading(true)
    setConfirmOpen(false)
    try {
      const base = getApiBase()
      const token = getAuthToken()
      const contextId = sessionStorage.getItem('active_context_id') ?? ''
      const res = await fetch(`${base}/api/v1/broadcast/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          context_id: contextId,
          message_template: broadcastMessage,
          mode: broadcastMode,
          channels: ['portal', 'whatsapp'],
        }),
      })
      if (!res.ok) {
        let detail = `Broadcast falhou: ${res.status}`
        try {
          const body = (await res.json()) as { detail?: string }
          if (body?.detail) detail = body.detail
        } catch {
          // body wasn't JSON — keep status-only message
        }
        throw new Error(detail)
      }
      const data = (await res.json()) as { whatsapp_sent: number; failures: number }
      setStats((prev) => ({
        ...prev,
        enviados: data.whatsapp_sent,
        falhas: data.failures,
      }))
      dispatch({ type: 'COMPLETE', index: 4 })
    } catch (err) {
      setBroadcastError(err instanceof Error ? err.message : 'Erro ao disparar.')
      dispatch({ type: 'ERROR', index: 4 })
    } finally {
      setBroadcastLoading(false)
    }
  }

  // ─── Stepper data ────────────────────────────────────────────────────────

  const stepperSteps = [
    { label: 'Upload\nEstudantes', status: steps[0].status },
    { label: 'Upload\nNotas', status: steps[1].status },
    { label: 'Gerar\nMatch', status: steps[2].status },
    { label: 'QR\nWhatsApp', status: steps[3].status },
    { label: 'Disparar', status: steps[4].status },
  ]

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <AppHeader activeTab="painel" />
      <ContextBar />

      <main className="max-w-7xl mx-auto px-6 py-6">
        {/* Progress Stepper */}
        <ProgressStepper steps={stepperSteps} />

        {/* 2-column layout */}
        <div className="flex gap-6">
          {/* Left column — 70% */}
          <div className="flex-[7] flex flex-col gap-4 min-w-0">

            {/* Step 1 — Upload Estudantes */}
            <StepCard
              stepNumber={1}
              title="Upload Estudantes"
              status={steps[0].status}
              preconditions={
                steps[0].status === 'locked'
                  ? ['Seleccionar contexto académico']
                  : undefined
              }
            >
              <p className="text-sm text-slate-600 mb-3">
                Importe a lista de estudantes em formato CSV.
              </p>
              {steps[0].status === 'completed' ? (
                <div className="flex items-center gap-2 text-sm text-[#15803D]">
                  <span>✅</span>
                  <span>
                    <strong>{stats.estudantes}</strong> estudantes importados
                  </span>
                  <button
                    type="button"
                    onClick={() => dispatch({ type: 'RESET' })}
                    className="ml-4 text-xs text-slate-400 hover:text-[#0D6EFD] underline"
                  >
                    Reiniciar
                  </button>
                </div>
              ) : (
                <FileDropzone
                  onFileSelect={handleStudentsUpload}
                  isLoading={step1Loading}
                  error={step1Error}
                  label="Arraste o CSV de estudantes ou clique para seleccionar"
                />
              )}
            </StepCard>

            {/* Step 2 — Upload Notas */}
            <StepCard
              stepNumber={2}
              title="Upload Notas"
              status={steps[1].status}
              preconditions={
                steps[1].status === 'locked'
                  ? ['Passo 1 completo: estudantes importados']
                  : undefined
              }
            >
              <p className="text-sm text-slate-600 mb-3">
                Importe o ficheiro CSV com as notas dos estudantes.
              </p>
              {steps[1].status === 'completed' ? (
                <div className="flex items-center gap-2 text-sm text-[#15803D]">
                  <span>✅</span>
                  <span>
                    <strong>{stats.notas}</strong> notas importadas
                  </span>
                </div>
              ) : (
                <FileDropzone
                  onFileSelect={handleGradesUpload}
                  isLoading={step2Loading}
                  error={step2Error}
                  label="Arraste o CSV de notas ou clique para seleccionar"
                />
              )}
            </StepCard>

            {/* Step 3 — Gerar Match */}
            <StepCard
              stepNumber={3}
              title="Gerar Match"
              status={steps[2].status}
              preconditions={
                steps[2].status === 'locked'
                  ? ['Passo 1 completo: estudantes importados', 'Passo 2 completo: notas importadas']
                  : undefined
              }
            >
              <p className="text-sm text-slate-600 mb-3">
                Cruza os estudantes com as notas e valida os números de telefone.
              </p>

              {steps[2].status === 'completed' && matchTimestamp && (
                <div className="flex items-center gap-2 text-xs text-slate-500 mb-3">
                  <span>🕒</span>
                  <span>Último match: {matchTimestamp}</span>
                </div>
              )}

              {matchResults.length > 0 && (
                <div className="mb-3">
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <Table aria-label="Resultados do match">
                      <TableHeader>
                        <TableRow>
                          <TableHead>Nº Estudante</TableHead>
                          <TableHead>Nome</TableHead>
                          <TableHead>Nota</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {matchResults.slice(0, 5).map((r) => (
                          <TableRow key={r.student_number}>
                            <TableCell className="font-mono text-sm">{r.student_number}</TableCell>
                            <TableCell>{r.name}</TableCell>
                            <TableCell>{r.grade !== null ? r.grade : '—'}</TableCell>
                            <TableCell>
                              <MatchStatusBadge status={r.status} />
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  {matchResults.length > 5 && (
                    <button
                      type="button"
                      onClick={() => setMatchDialogOpen(true)}
                      className="mt-2 text-sm text-[#0D6EFD] hover:underline"
                    >
                      Ver todos ({matchResults.length} resultados)
                    </button>
                  )}
                </div>
              )}

              {steps[2].status !== 'completed' && (
                <>
                  {step3Error && (
                    <p
                      role="alert"
                      className="mb-3 text-sm text-[#B91C1C] bg-red-50 border border-red-200 rounded-md px-3 py-2"
                    >
                      {step3Error}
                    </p>
                  )}
                  <Button
                    onClick={handleMatch}
                    disabled={step3Loading}
                    className="bg-[#0D6EFD] hover:bg-[#0D6EFD]/90 text-white"
                  >
                    {step3Loading ? '⏳ A gerar match…' : '🔍 Gerar Match'}
                  </Button>
                </>
              )}
            </StepCard>

            {/* Step 4 — QR WhatsApp */}
            <StepCard
              stepNumber={4}
              title="QR WhatsApp"
              status={steps[3].status}
              preconditions={
                steps[3].status === 'locked'
                  ? [
                      'Passo 1 completo: estudantes importados',
                      'Passo 2 completo: notas importadas',
                      'Passo 3 completo: match gerado',
                    ]
                  : undefined
              }
            >
              {/* Sub-steps */}
              <div className="flex items-center gap-2 mb-4">
                {['Criar', 'Conectar', 'Verificar'].map((label, i) => {
                  const isDone = qrConnected && i < 2
                  const isActive = !qrConnected && i === 0
                  return (
                    <div key={label} className="flex items-center gap-2">
                      <div className="flex items-center gap-1">
                        <div
                          className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
                            isDone
                              ? 'bg-[#15803D] text-white'
                              : isActive
                              ? 'bg-[#0D6EFD] text-white animate-pulse'
                              : 'bg-slate-200 text-slate-500'
                          }`}
                        >
                          {isDone ? '✓' : i + 1}
                        </div>
                        <span
                          className={`text-xs ${
                            isDone
                              ? 'text-[#15803D] font-medium'
                              : isActive
                              ? 'text-[#0D6EFD] font-medium'
                              : 'text-slate-400'
                          }`}
                        >
                          {label}
                        </span>
                      </div>
                      {i < 2 && (
                        <div
                          className={`w-8 h-0.5 ${isDone ? 'bg-[#15803D]' : 'bg-slate-200'}`}
                          aria-hidden="true"
                        />
                      )}
                    </div>
                  )
                })}
              </div>

              {qrConnected ? (
                <div className="flex items-center gap-2 text-sm text-[#15803D]">
                  <span>✅</span>
                  <span>WhatsApp conectado! A avançar para o passo seguinte…</span>
                </div>
              ) : (
                <div className="flex flex-col items-start gap-4 sm:flex-row">
                  {/* QR Placeholder */}
                  <div
                    className="relative w-44 h-44 border-2 border-slate-300 rounded-lg flex items-center justify-center bg-white overflow-hidden flex-shrink-0"
                    aria-label="QR Code placeholder"
                    role="img"
                  >
                    {/* Dot-pattern QR placeholder */}
                    <div className="grid grid-cols-9 gap-0.5 p-2">
                      {Array.from({ length: 81 }).map((_, i) => (
                        <div
                          key={i}
                          className={`w-3.5 h-3.5 rounded-sm ${
                            (i % 3 === 0 || i % 7 === 0 || i % 11 === 0)
                              ? 'bg-slate-900'
                              : 'bg-white'
                          }`}
                        />
                      ))}
                    </div>
                    {qrExpired && (
                      <div className="absolute inset-0 bg-white/90 flex flex-col items-center justify-center gap-2">
                        <span className="text-2xl">⏱️</span>
                        <span className="text-xs text-slate-600 font-medium text-center">
                          QR expirado
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Info & countdown */}
                  <div className="flex flex-col gap-3">
                    <p className="text-sm text-slate-600">
                      Leia o QR code com a câmara do WhatsApp para conectar.
                    </p>

                    {!qrExpired ? (
                      <div className="flex items-center gap-2">
                        <div
                          className={`text-lg font-bold tabular-nums ${
                            countdown <= 10 ? 'text-[#B91C1C]' : 'text-[#0D6EFD]'
                          }`}
                          aria-live="polite"
                          aria-label={`${countdown} segundos restantes`}
                        >
                          {countdown}s
                        </div>
                        <span className="text-xs text-slate-500">restantes</span>
                      </div>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRefreshQr}
                        className="text-[#0D6EFD] border-[#0D6EFD] hover:bg-[#0D6EFD]/5 self-start"
                      >
                        🔄 Gerar novo QR
                      </Button>
                    )}

                    <p className="text-xs text-slate-400">
                      Polling automático a cada 5s. A conexão é simulada automaticamente após 8s.
                    </p>
                  </div>
                </div>
              )}
            </StepCard>

            {/* Step 5 — Disparar */}
            <StepCard
              stepNumber={5}
              title="Disparar Notificações"
              status={steps[4].status}
              preconditions={
                steps[4].status === 'locked'
                  ? [
                      'Passo 1 completo: estudantes importados',
                      'Passo 2 completo: notas importadas',
                      'Passo 3 completo: match gerado',
                      'Passo 4 completo: WhatsApp conectado',
                    ]
                  : undefined
              }
            >
              {steps[4].status === 'completed' ? (
                <div className="flex flex-col gap-2 text-sm text-[#15803D]">
                  <div className="flex items-center gap-2">
                    <span>✅</span>
                    <span>
                      <strong>{stats.enviados}</strong> mensagens enviadas
                      {stats.falhas > 0 && (
                        <span className="text-[#B91C1C] ml-2">({stats.falhas} falhas)</span>
                      )}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  {/* Message template */}
                  <div>
                    <Label htmlFor="broadcast-template" className="text-sm font-medium text-slate-700 mb-1.5 block">
                      Template da mensagem
                    </Label>
                    <textarea
                      id="broadcast-template"
                      value={broadcastMessage}
                      onChange={(e) => setBroadcastMessage(e.target.value)}
                      rows={3}
                      className="w-full rounded-md border border-input bg-white px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 resize-none"
                      placeholder="Olá {nome}! A sua nota é {nota}."
                    />
                    <p className="text-xs text-slate-400 mt-1">
                      Variáveis: <code className="bg-slate-100 px-1 rounded">{'{nome}'}</code>{' '}
                      <code className="bg-slate-100 px-1 rounded">{'{nota}'}</code>{' '}
                      <code className="bg-slate-100 px-1 rounded">{'{disciplina}'}</code>
                    </p>
                  </div>

                  {/* Mode selection */}
                  <div className="flex flex-col gap-2">
                    <p className="text-sm font-medium text-slate-700">Modo de envio</p>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="broadcast-mode"
                          value="simulation"
                          checked={broadcastMode === 'simulation'}
                          onChange={() => setBroadcastMode('simulation')}
                          className="accent-[#0D6EFD]"
                        />
                        <span className="text-sm text-slate-700">🧪 Simulação</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="broadcast-mode"
                          value="real"
                          checked={broadcastMode === 'real'}
                          onChange={() => setBroadcastMode('real')}
                          className="accent-[#0D6EFD]"
                        />
                        <span className="text-sm text-slate-700">🚀 Envio Real</span>
                      </label>
                    </div>
                    {broadcastMode === 'real' && (
                      <p className="text-xs text-[#B45309] bg-amber-50 border border-amber-200 rounded px-3 py-2">
                        ⚠️ O modo real enviará mensagens WhatsApp reais a <strong>{stats.matched}</strong> estudantes.
                      </p>
                    )}
                  </div>

                  {broadcastError && (
                    <p
                      role="alert"
                      className="text-sm text-[#B91C1C] bg-red-50 border border-red-200 rounded-md px-3 py-2"
                    >
                      {broadcastError}
                    </p>
                  )}

                  <div className="flex items-center gap-3 flex-wrap">
                    <Button
                      onClick={handleBroadcastClick}
                      disabled={broadcastLoading}
                      className="bg-[#0D6EFD] hover:bg-[#0D6EFD]/90 text-white self-start"
                    >
                      {broadcastLoading ? '⏳ A enviar…' : '🚀 Disparar'}
                    </Button>
                    <button
                      type="button"
                      onClick={() => {
                        const ctxId = sessionStorage.getItem('active_context_id') ?? ''
                        navigate(`/publicar${ctxId ? `?context=${ctxId}` : ''}`)
                      }}
                      className="text-sm text-[#0D6EFD] hover:underline"
                    >
                      ⑤ Usar Assistente de Publicação →
                    </button>
                  </div>
                </div>
              )}
            </StepCard>
          </div>

          {/* Right column — 30% */}
          <div className="flex-[3] min-w-[240px]">
            <QuickStatsSidebar stats={stats} />
          </div>
        </div>
      </main>

      {/* Dialog — Ver todos os resultados do match */}
      <Dialog open={matchDialogOpen} onOpenChange={setMatchDialogOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Todos os Resultados do Match</DialogTitle>
          </DialogHeader>
          <div className="max-h-96 overflow-y-auto">
            <Table aria-label="Todos os resultados do match">
              <TableHeader>
                <TableRow>
                  <TableHead>Nº Estudante</TableHead>
                  <TableHead>Nome</TableHead>
                  <TableHead>Nota</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {matchResults.map((r) => (
                  <TableRow key={r.student_number}>
                    <TableCell className="font-mono text-sm">{r.student_number}</TableCell>
                    <TableCell>{r.name}</TableCell>
                    <TableCell>{r.grade !== null ? r.grade : '—'}</TableCell>
                    <TableCell>
                      <MatchStatusBadge status={r.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMatchDialogOpen(false)}>
              Fechar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Dialog — Confirmação Envio Real */}
      <Dialog open={confirmOpen} onOpenChange={(open) => { if (!open) setConfirmOpen(false) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>⚠️ Confirmar Envio Real</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4">
            <p className="text-sm text-slate-700">
              Está prestes a enviar mensagens WhatsApp reais a{' '}
              <strong className="text-slate-900">{stats.matched} destinatários</strong>.
              Esta acção não pode ser revertida.
            </p>
            <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
              <p className="text-sm text-[#B45309] font-medium">
                ⚠️ Aviso: os destinatários receberão mensagens reais no WhatsApp.
                Certifique-se de que os dados estão correctos antes de confirmar.
              </p>
            </div>
            <label className="flex items-start gap-3 cursor-pointer">
              <Checkbox
                id="confirm-send"
                checked={confirmChecked}
                onCheckedChange={(checked) => setConfirmChecked(checked === true)}
                className="mt-0.5"
              />
              <span className="text-sm text-slate-700" id="confirm-send-label">
                Confirmo que os dados estão correctos e autorizo o envio das mensagens.
              </span>
            </label>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmOpen(false)}
              disabled={broadcastLoading}
            >
              Cancelar
            </Button>
            <Button
              onClick={executeBroadcast}
              disabled={!confirmChecked || broadcastLoading}
              className="bg-[#0D6EFD] hover:bg-[#0D6EFD]/90 text-white"
            >
              {broadcastLoading ? '⏳ A enviar…' : 'Confirmar Envio Real'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
