import { useEffect, useReducer, useRef, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { CheckCircle, XCircle, AlertTriangle, Search, Rocket, RefreshCw, Clock, ArrowRight } from 'lucide-react'
import { AppHeader } from '@/components/organisms/AppHeader'
import { FileDropzone } from '@/components/molecules/FileDropzone'
import { useActiveContext } from '@/contexts/ActiveContextContext'
import { apiFetch } from '@/lib/api'
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
  return (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? ''
}

// ─── Status badge helper ──────────────────────────────────────────────────────

function MatchStatusBadge({ status }: { status: MatchResult['status'] }) {
  if (status === 'matched') return <span className="text-success font-medium flex items-center gap-1"><CheckCircle className="size-3.5" /> Match</span>
  if (status === 'no_grade') return <span className="text-destructive font-medium flex items-center gap-1"><XCircle className="size-3.5" /> Sem nota</span>
  return <span className="text-warning font-medium flex items-center gap-1"><AlertTriangle className="size-3.5" /> Sem telefone</span>
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function ProfessorDashboardPage() {
  const navigate = useNavigate()
  const { activeContextId } = useActiveContext()

  // Step state
  const [steps, dispatch] = useReducer(stepReducer, undefined, loadState)

  // WhatsApp reconnect (status polling handled by QuickStatsSidebar)
  const [waReconnecting, setWaReconnecting] = useState(false)

  const handleWaReconnect = useCallback(async () => {
    setWaReconnecting(true)
    try {
      await apiFetch('/api/v1/whatsapp/setup/create', { method: 'POST' })
    } catch {
      // non-fatal
    } finally {
      setWaReconnecting(false)
    }
  }, [])

  // Quick stats — pre-populated from DB on mount
  const [stats, setStats] = useState<QuickStats>(INITIAL_STATS)

  useEffect(() => {
    apiFetch<{ totalStudents: number; publishedGrades: number }>(
      '/api/v1/delegado/system-status',
    )
      .then((data) =>
        setStats((prev) => ({
          ...prev,
          estudantes: data.totalStudents ?? 0,
          notas: data.publishedGrades ?? 0,
        })),
      )
      .catch(() => { /* non-fatal */ })
  }, [])

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
  const [countdown, setCountdown] = useState(60)
  const [qrExpired, setQrExpired] = useState(false)
  const [qrConnected, setQrConnected] = useState(false)
  const [qrCode, setQrCode] = useState<string | null>(null)
  const [qrLoading, setQrLoading] = useState(false)
  const [qrError, setQrError] = useState<string | null>(null)
  const [waConfigStatus, setWaConfigStatus] = useState<{ configured: boolean; reachable: boolean } | null>(null)
  const [waConfigChecking, setWaConfigChecking] = useState(false)
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const qrPollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const statusPollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Step 5 — Disparar
  const [broadcastMode, setBroadcastMode] = useState<'simulation' | 'real'>('simulation')
  const [broadcastMessage, setBroadcastMessage] = useState(
    'Olá {nome}! A sua nota de {disciplina} é {nota}. Cumprimentos.',
  )
  const [broadcastLoading, setBroadcastLoading] = useState(false)
  const [broadcastError, setBroadcastError] = useState<string | undefined>()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [confirmChecked, setConfirmChecked] = useState(false)

  // ─── Config status check ────────────────────────────────────────────────

  const checkConfigStatus = useCallback(async (): Promise<{ configured: boolean; reachable: boolean }> => {
    setWaConfigChecking(true)
    try {
      const data = await apiFetch<{ configured: boolean; reachable: boolean }>(
        '/api/v1/whatsapp/setup/config-status',
      )
      setWaConfigStatus(data)
      return data
    } catch {
      const fallback = { configured: false, reachable: false }
      setWaConfigStatus(fallback)
      return fallback
    } finally {
      setWaConfigChecking(false)
    }
  }, [])

  // ─── QR fetch and polling ───────────────────────────────────────────────

  const fetchQrCode = useCallback(async () => {
    setQrLoading(true)
    setQrError(null)
    try {
      // Ensure the professor's instance exists before requesting QR
      await apiFetch('/api/v1/whatsapp/setup/create', { method: 'POST' }).catch(() => {})
      const data = await apiFetch<{ code: string | null; simulated?: boolean }>(
        '/api/v1/whatsapp/setup/qr',
      )
      const isImageCode = data.code && (data.code.startsWith('data:') || data.code.startsWith('http'))
      if (isImageCode) {
        setQrCode(data.code)
        setQrExpired(false)
        if (countdownRef.current) clearInterval(countdownRef.current)
        setCountdown(60)
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
      } else if (data.simulated) {
        setQrCode(null)
        setQrError('Evolution API não configurada. Defina EVOLUTION_API_URL nas variáveis de ambiente do Railway.')
      } else if (data.code) {
        // code exists but is not a renderable image (raw QR string from Evolution API)
        setQrCode(null)
        setQrError('QR recebido num formato não suportado. Verifique a versão da Evolution API.')
      } else {
        setQrCode(null)
        setQrError('Evolution API não respondeu. Verifique se o serviço está a correr.')
      }
    } catch {
      setQrCode(null)
      setQrError('Erro ao contactar a Evolution API. Verifique a configuração.')
    } finally {
      setQrLoading(false)
    }
  }, [])

  const checkWaConnected = useCallback(async () => {
    try {
      const data = await apiFetch<{ connected: boolean }>('/api/v1/whatsapp/setup/status')
      if (data.connected) {
        setQrConnected(true)
        if (countdownRef.current) clearInterval(countdownRef.current)
        if (qrPollRef.current) clearInterval(qrPollRef.current)
        if (statusPollRef.current) clearInterval(statusPollRef.current)
      }
    } catch {
      // non-fatal
    }
  }, [])

  const startCountdown = useCallback(() => {
    // Clear existing timers
    if (countdownRef.current) clearInterval(countdownRef.current)
    if (qrPollRef.current) clearInterval(qrPollRef.current)
    if (statusPollRef.current) clearInterval(statusPollRef.current)
    setQrConnected(false)

    // Fetch QR immediately, then every 5s for fresh codes
    void fetchQrCode()
    qrPollRef.current = setInterval(() => { void fetchQrCode() }, 5000)

    // Poll connection status every 5s to detect when user scans
    statusPollRef.current = setInterval(() => { void checkWaConnected() }, 5000)
  }, [fetchQrCode, checkWaConnected])

  useEffect(() => {
    if (steps[3].status !== 'active') return
    const initTimer = setTimeout(async () => {
      const cfg = await checkConfigStatus()
      if (cfg.configured && cfg.reachable && !qrConnected) {
        startCountdown()
      }
    }, 0)
    return () => {
      clearTimeout(initTimer)
      if (countdownRef.current) clearInterval(countdownRef.current)
      if (qrPollRef.current) clearInterval(qrPollRef.current)
      if (statusPollRef.current) clearInterval(statusPollRef.current)
    }
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
      const contextId = activeContextId ?? ''
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
      const contextId = activeContextId ?? ''
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
      const contextId = activeContextId ?? ''
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
    setQrExpired(false)
    setQrCode(null)
    setQrError(null)
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
      const contextId = activeContextId ?? ''
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
    <div className="min-h-screen bg-background">
      <AppHeader activeTab="painel" />

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
              <p className="text-sm text-muted-foreground mb-3">
                Importe a lista de estudantes em formato CSV.
              </p>
              {steps[0].status === 'completed' ? (
                <div className="flex items-center gap-2 text-sm text-success">
                  <CheckCircle className="size-4 shrink-0" />
                  <span>
                    <strong>{stats.estudantes}</strong> estudantes importados
                  </span>
                  <button
                    type="button"
                    onClick={() => dispatch({ type: 'RESET' })}
                    className="ml-4 text-xs text-muted-foreground hover:text-primary underline"
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
              <p className="text-sm text-muted-foreground mb-3">
                Importe o ficheiro CSV com as notas dos estudantes.
              </p>
              {steps[1].status === 'completed' ? (
                <div className="flex items-center gap-2 text-sm text-success">
                  <CheckCircle className="size-4 shrink-0" />
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
              <p className="text-sm text-muted-foreground mb-3">
                Cruza os estudantes com as notas e valida os números de telefone.
              </p>

              {steps[2].status === 'completed' && matchTimestamp && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                  <Clock className="size-3 shrink-0" />
                  <span>Último match: {matchTimestamp}</span>
                </div>
              )}

              {matchResults.length > 0 && (
                <div className="mb-3">
                  <div className="border border-border rounded-lg overflow-hidden">
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
                      className="mt-2 text-sm text-primary hover:underline"
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
                      className="mb-3 text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md px-3 py-2"
                    >
                      {step3Error}
                    </p>
                  )}
                  <Button
                    onClick={handleMatch}
                    disabled={step3Loading}
                    className="bg-primary hover:bg-primary/90 text-primary-foreground"
                  >
                    {step3Loading
                      ? <><RefreshCw className="size-4 animate-spin" /> A gerar match…</>
                      : <><Search className="size-4" /> Gerar Match</>
                    }
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
                              ? 'bg-success text-white'
                              : isActive
                              ? 'bg-primary text-white animate-pulse'
                              : 'bg-muted text-muted-foreground'
                          }`}
                        >
                          {isDone ? <CheckCircle className="size-3.5" /> : i + 1}
                        </div>
                        <span
                          className={`text-xs ${
                            isDone
                              ? 'text-success font-medium'
                              : isActive
                              ? 'text-primary font-medium'
                              : 'text-muted-foreground'
                          }`}
                        >
                          {label}
                        </span>
                      </div>
                      {i < 2 && (
                        <div
                          className={`w-8 h-0.5 ${isDone ? 'bg-success' : 'bg-muted'}`}
                          aria-hidden="true"
                        />
                      )}
                    </div>
                  )
                })}
              </div>

              {qrConnected ? (
                <div className="flex items-center gap-2 text-sm text-success">
                  <CheckCircle className="size-4 shrink-0" />
                  <span>WhatsApp conectado! A avançar para o passo seguinte…</span>
                </div>
              ) : waConfigChecking ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <RefreshCw className="size-4 animate-spin" />
                  <span>A verificar configuração da Evolution API…</span>
                </div>
              ) : waConfigStatus && !waConfigStatus.configured ? (
                <div className="flex flex-col gap-3">
                  <div role="alert" className="bg-destructive/10 border border-destructive/20 rounded-md px-4 py-3 text-sm text-destructive">
                    <p className="font-semibold mb-1">Evolution API não configurada</p>
                    <p className="text-xs text-destructive/80">
                      Para enviar notificações WhatsApp, é necessário adicionar um serviço Evolution API ao Railway e configurar as seguintes variáveis de ambiente neste serviço:
                    </p>
                  </div>
                  <div className="bg-muted rounded-md px-4 py-3 text-xs font-mono space-y-1">
                    <p><span className="text-primary">EVOLUTION_API_URL</span>=https://&lt;seu-serviço-evolution&gt;.railway.app</p>
                    <p><span className="text-primary">EVOLUTION_API_KEY</span>=&lt;chave-secreta&gt;</p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    No Railway: adicione um novo serviço com a imagem <code className="bg-muted px-1 rounded">atendai/evolution-api:latest</code>, configure as variáveis acima, e defina <code className="bg-muted px-1 rounded">RAILWAY_PUBLIC_DOMAIN</code> ou <code className="bg-muted px-1 rounded">APP_URL</code> neste serviço para que o webhook seja configurado automaticamente.
                  </p>
                </div>
              ) : waConfigStatus && waConfigStatus.configured && !waConfigStatus.reachable ? (
                <div className="flex flex-col gap-3">
                  <div role="alert" className="bg-warning/10 border border-warning/20 rounded-md px-4 py-3 text-sm text-warning">
                    <p className="font-semibold mb-1">Evolution API inacessível</p>
                    <p className="text-xs">
                      A variável <code className="bg-warning/20 px-1 rounded">EVOLUTION_API_URL</code> está definida mas o serviço não está a responder. Verifique se o serviço Evolution API está a correr no Railway.
                    </p>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => { void checkConfigStatus().then((cfg) => { if (cfg.configured && cfg.reachable) startCountdown() }) }}
                    className="self-start gap-2"
                  >
                    <RefreshCw className="size-4" /> Tentar novamente
                  </Button>
                </div>
              ) : (
                <div className="flex flex-col items-start gap-4 sm:flex-row">
                  {/* QR Code — real image from Evolution API */}
                  <div
                    className="relative w-44 h-44 border-2 border-border rounded-lg flex items-center justify-center bg-card overflow-hidden flex-shrink-0"
                    aria-label="QR Code WhatsApp"
                    role="img"
                  >
                    {qrLoading && !qrCode && (
                      <RefreshCw className="size-6 text-muted-foreground animate-spin" />
                    )}
                    {qrCode && !qrExpired && (
                      <img
                        src={qrCode}
                        alt="QR WhatsApp"
                        className="w-44 h-44 object-contain"
                      />
                    )}
                    {qrExpired && (
                      <div className="absolute inset-0 bg-card/90 flex flex-col items-center justify-center gap-2">
                        <Clock className="size-6 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground font-medium text-center">
                          QR expirado
                        </span>
                      </div>
                    )}
                    {!qrLoading && !qrCode && !qrExpired && qrError && (
                      <div className="flex flex-col items-center justify-center gap-2 p-2">
                        <AlertTriangle className="size-5 text-warning" />
                        <span className="text-xs text-muted-foreground text-center">
                          {qrError}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Info & countdown */}
                  <div className="flex flex-col gap-3">
                    <p className="text-sm text-muted-foreground">
                      Leia o QR code com a câmara do WhatsApp para conectar.
                    </p>

                    {!qrExpired && qrCode ? (
                      <div className="flex items-center gap-2">
                        <div
                          className={`text-lg font-bold tabular-nums ${
                            countdown <= 10 ? 'text-destructive' : 'text-primary'
                          }`}
                          aria-live="polite"
                          aria-label={`${countdown} segundos restantes`}
                        >
                          {countdown}s
                        </div>
                        <span className="text-xs text-muted-foreground">restantes</span>
                      </div>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRefreshQr}
                        className="text-primary border-primary hover:bg-primary/5 self-start gap-2"
                      >
                        <RefreshCw className="size-4" /> Gerar novo QR
                      </Button>
                    )}

                    <p className="text-xs text-muted-foreground">
                      Polling automático a cada 5s. A leitura do QR activa a ligação.
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
                <div className="flex flex-col gap-2 text-sm text-success">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="size-4 shrink-0" />
                    <span>
                      <strong>{stats.enviados}</strong> mensagens enviadas
                      {stats.falhas > 0 && (
                        <span className="text-destructive ml-2">({stats.falhas} falhas)</span>
                      )}
                    </span>
                  </div>
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  {/* Message template */}
                  <div>
                    <Label htmlFor="broadcast-template" className="text-sm font-medium text-foreground mb-1.5 block">
                      Template da mensagem
                    </Label>
                    <textarea
                      id="broadcast-template"
                      value={broadcastMessage}
                      onChange={(e) => setBroadcastMessage(e.target.value)}
                      rows={3}
                      className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm shadow-xs outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 resize-none"
                      placeholder="Olá {nome}! A sua nota é {nota}."
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Variáveis: <code className="bg-muted px-1 rounded">{'{nome}'}</code>{' '}
                      <code className="bg-muted px-1 rounded">{'{nota}'}</code>{' '}
                      <code className="bg-muted px-1 rounded">{'{disciplina}'}</code>
                    </p>
                  </div>

                  {/* Mode selection */}
                  <div className="flex flex-col gap-2">
                    <p className="text-sm font-medium text-foreground">Modo de envio</p>
                    <div className="flex gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="broadcast-mode"
                          value="simulation"
                          checked={broadcastMode === 'simulation'}
                          onChange={() => setBroadcastMode('simulation')}
                          className="accent-primary"
                        />
                        <span className="text-sm text-foreground flex items-center gap-1.5"><AlertTriangle className="size-3.5 text-warning" /> Simulação</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input
                          type="radio"
                          name="broadcast-mode"
                          value="real"
                          checked={broadcastMode === 'real'}
                          onChange={() => setBroadcastMode('real')}
                          className="accent-primary"
                        />
                        <span className="text-sm text-foreground flex items-center gap-1.5"><Rocket className="size-3.5 text-primary" /> Envio Real</span>
                      </label>
                    </div>
                    {broadcastMode === 'real' && (
                      <p className="text-xs text-warning bg-warning/10 border border-warning/20 rounded px-3 py-2 flex items-center gap-2">
                        <AlertTriangle className="size-3.5 shrink-0" /> O modo real enviará mensagens WhatsApp reais a <strong>{stats.matched}</strong> estudantes.
                      </p>
                    )}
                  </div>

                  {broadcastError && (
                    <p
                      role="alert"
                      className="text-sm text-destructive bg-destructive/10 border border-destructive/20 rounded-md px-3 py-2"
                    >
                      {broadcastError}
                    </p>
                  )}

                  <div className="flex items-center gap-3 flex-wrap">
                    <Button
                      onClick={handleBroadcastClick}
                      disabled={broadcastLoading}
                      className="bg-primary hover:bg-primary/90 text-primary-foreground self-start"
                    >
                      {broadcastLoading
                        ? <><RefreshCw className="size-4 animate-spin" /> A enviar…</>
                        : <><Rocket className="size-4" /> Disparar</>
                      }
                    </Button>
                    <button
                      type="button"
                      onClick={() => {
                        navigate(`/publicar${activeContextId ? `?context=${activeContextId}` : ''}`)
                      }}
                      className="text-sm text-primary hover:underline"
                    >
                      <ArrowRight className="size-4" /> Usar Assistente de Publicação
                    </button>
                  </div>
                </div>
              )}
            </StepCard>
          </div>

          {/* Right column — 30% */}
          <div className="flex-[3] min-w-[240px] flex flex-col gap-4">
            <QuickStatsSidebar stats={stats} onReconnect={handleWaReconnect} reconnecting={waReconnecting} />
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
            <DialogTitle className="flex items-center gap-2"><AlertTriangle className="size-5 text-warning" /> Confirmar Envio Real</DialogTitle>
          </DialogHeader>
          <div className="flex flex-col gap-4">
            <p className="text-sm text-foreground">
              Está prestes a enviar mensagens WhatsApp reais a{' '}
              <strong className="text-foreground">{stats.matched} destinatários</strong>.
              Esta acção não pode ser revertida.
            </p>
            <div className="bg-warning/10 border border-warning/20 rounded-lg px-4 py-3">
              <p className="text-sm text-warning font-medium flex items-start gap-2">
                <AlertTriangle className="size-4 shrink-0 mt-0.5" />
                Aviso: os destinatários receberão mensagens reais no WhatsApp.
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
              <span className="text-sm text-foreground" id="confirm-send-label">
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
              className="bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              {broadcastLoading
                ? <><RefreshCw className="size-4 animate-spin" /> A enviar…</>
                : 'Confirmar Envio Real'
              }
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
