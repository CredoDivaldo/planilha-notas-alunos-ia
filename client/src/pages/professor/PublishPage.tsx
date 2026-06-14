// PublishPage — /publicar — 4-step publication wizard (Story 7.7)
// AC1-AC14: stepper, audience, channels, confirm, result screen, WhatsApp status, accessibility

import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { CheckCircle, AlertTriangle, Rocket, RefreshCw, ChevronLeft } from 'lucide-react'
import { useActiveContext } from '@/contexts/ActiveContextContext'
import { WizardLayout } from '@/layouts/WizardLayout'
import { PublicationStepper } from '@/components/organisms/PublicationStepper'
import type { PublicationStepState } from '@/components/organisms/PublicationStepper'
import { BroadcastResultSummary } from '@/components/organisms/BroadcastResultSummary'
import type { BroadcastResult } from '@/components/organisms/BroadcastResultSummary'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Checkbox } from '@/components/ui/checkbox'
import { apiFetch } from '@/lib/api'
import { calcNotaFinal, getRowBadgeLabel } from '@/lib/grades'
import type { ContextItem, StudentRow } from '@/types'


// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type AudienceType = 'all' | 'approved' | 'rejected' | 'manual'
type ChannelType = 'whatsapp' | 'portal_only'

interface WhatsAppStatus {
  connected: boolean
  instanceName: string
}

// Default message template with placeholders
const DEFAULT_TEMPLATE = `Olá {{nome}}! A sua nota de {{disciplina}} ({{semestre}}) é {{nota_final}}. Resultado: {{resultado}}. Cumprimentos.`

// ---------------------------------------------------------------------------
// Helper: derive student with computed nota
// ---------------------------------------------------------------------------

interface StudentWithNota {
  row: StudentRow
  nota: number | null
  badge: string
  complete: boolean
  hasPhone: boolean
}

// ---------------------------------------------------------------------------
// Result badge helper
// ---------------------------------------------------------------------------

function ResultBadge({ nota }: { nota: number | null }) {
  if (nota === null) return <span className="text-xs bg-warning/10 text-warning px-2 py-0.5 rounded-full">Incompleta</span>
  if (nota >= 10) return <span className="text-xs bg-success/10 text-success px-2 py-0.5 rounded-full flex items-center gap-1 w-fit"><CheckCircle className="size-3" /> Aprovado</span>
  return <span className="text-xs bg-destructive/10 text-destructive px-2 py-0.5 rounded-full">Reprovado</span>
}

// ---------------------------------------------------------------------------
// Live preview helper
// ---------------------------------------------------------------------------

function renderPreview(template: string, student: StudentWithNota, disciplina: string, semestre: string): string {
  if (!student) return template
  const nota = student.nota !== null ? String(student.nota) : '—'
  const resultado = student.nota !== null ? (student.nota >= 10 ? 'Aprovado' : 'Reprovado') : '—'
  return template
    .replace(/{{nome}}/g, student.row.studentName)
    .replace(/{{disciplina}}/g, disciplina)
    .replace(/{{semestre}}/g, semestre)
    .replace(/{{nota_final}}/g, nota)
    .replace(/{{resultado}}/g, resultado)
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function PublishPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { activeContextId } = useActiveContext()

  // T10: context propagation via ?context={id}, falling back to global active context
  const contextId = searchParams.get('context') ?? activeContextId ?? null

  // Data
  const [contextItem, setContextItem] = useState<ContextItem | null>(null)
  const [rows, setRows] = useState<StudentRow[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // T11: WhatsApp status
  const [waStatus, setWaStatus] = useState<WhatsAppStatus>({ connected: false, instanceName: 'whatsapp-instance' })
  const [waChecking, setWaChecking] = useState(false)
  const waPollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Wizard state
  const [currentStep, setCurrentStep] = useState(0) // 0-3
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set())

  // Step 2: audience
  const [audience, setAudience] = useState<AudienceType>('all')

  // Step 3: channels + template
  const [channels, setChannels] = useState<Set<ChannelType>>(new Set<ChannelType>(['portal_only']))
  const [messageTemplate, setMessageTemplate] = useState(DEFAULT_TEMPLATE)

  // Step 4: confirm checkbox
  const [confirmChecked, setConfirmChecked] = useState(false)

  // Publish state
  const [publishing, setPublishing] = useState(false)
  const [publishError, setPublishError] = useState<string | null>(null)
  const [publishResult, setPublishResult] = useState<BroadcastResult | null>(null)
  const [resending, setResending] = useState(false)

  // ---------------------------------------------------------------------------
  // Load data
  // ---------------------------------------------------------------------------

  const loadData = useCallback(async () => {
    if (!contextId) {
      setLoadError('Nenhum contexto académico seleccionado. Seleccione um contexto no topo da página.')
      setLoading(false)
      return
    }
    setLoadError(null)
    try {
      const ctx = await apiFetch<ContextItem>(`/academic-contexts/${contextId}`)
      setContextItem(ctx)
      const gradesData = await apiFetch<{ students: StudentRow[] }>(`/grades/?context_id=${contextId}`)
      setRows(gradesData.students ?? [])
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Erro ao carregar dados.')
      setContextItem(null)
      setRows([])
    } finally {
      setLoading(false)
    }
  }, [contextId])

  useEffect(() => { void loadData() }, [loadData])

  // T11: WhatsApp status polling
  const checkWaStatus = useCallback(async () => {
    setWaChecking(true)
    try {
      const data = await apiFetch<{ connected: boolean; instance_name: string }>('/api/v1/whatsapp/setup/status')
      setWaStatus({ connected: data.connected, instanceName: data.instance_name })
    } catch {
      // keep current
    } finally {
      setWaChecking(false)
    }
  }, [])

  useEffect(() => {
    const initTimer = setTimeout(() => { void checkWaStatus() }, 0)
    waPollingRef.current = setInterval(() => { void checkWaStatus() }, 30_000)
    return () => {
      clearTimeout(initTimer)
      if (waPollingRef.current) clearInterval(waPollingRef.current)
    }
  }, [checkWaStatus])

  // ---------------------------------------------------------------------------
  // Derived: students with computed data
  // ---------------------------------------------------------------------------

  const studentsWithNota = useMemo<StudentWithNota[]>(() =>
    rows.map((row) => {
      const components = contextItem?.components ?? []
      const nota = calcNotaFinal(row.components, components)
      const badge = getRowBadgeLabel(row.components, components, row.published)
      const complete = badge !== 'Incompleta' && badge !== 'Vazio'
      const hasPhone = !!(row.phone && row.phone.trim().length > 0)
      return { row, nota, badge, complete, hasPhone }
    }),
    [rows, contextItem],
  )

  const completeStudents = useMemo(
    () => studentsWithNota.filter((s) => s.complete),
    [studentsWithNota],
  )

  const incompleteStudents = useMemo(
    () => studentsWithNota.filter((s) => !s.complete),
    [studentsWithNota],
  )

  // T4: audience counts
  const audienceCounts = useMemo(() => {
    const all = completeStudents.length
    const approved = completeStudents.filter((s) => s.nota !== null && s.nota >= 10).length
    const rejected = completeStudents.filter((s) => s.nota !== null && s.nota < 10).length
    return { all, approved, rejected }
  }, [completeStudents])

  // Selected audience students
  const selectedStudents = useMemo(() => {
    if (audience === 'all') return completeStudents
    if (audience === 'approved') return completeStudents.filter((s) => s.nota !== null && s.nota >= 10)
    if (audience === 'rejected') return completeStudents.filter((s) => s.nota !== null && s.nota < 10)
    return completeStudents // manual — for now same as all
  }, [audience, completeStudents])

  const noPhoneCount = useMemo(
    () => selectedStudents.filter((s) => !s.hasPhone).length,
    [selectedStudents],
  )

  const effectiveRecipients = useMemo(
    () => selectedStudents.filter((s) => s.hasPhone),
    [selectedStudents],
  )

  // Preview with first student
  const previewText = useMemo(() => {
    const first = completeStudents[0]
    if (!first || !contextItem) return messageTemplate
    return renderPreview(messageTemplate, first, contextItem.disciplina, contextItem.semestre)
  }, [messageTemplate, completeStudents, contextItem])

  const breadcrumb = contextItem
    ? `${contextItem.turma} · ${contextItem.disciplina} · ${contextItem.semestre} · ${contextItem.turno}`
    : '—'

  // ---------------------------------------------------------------------------
  // Stepper state derivation
  // ---------------------------------------------------------------------------

  const stepStates = useMemo<{ label: string; state: PublicationStepState }[]>(() => {
    return [0, 1, 2, 3].map((i) => ({
      label: ['Revisão', 'Audiência', 'Canais', 'Confirmar'][i],
      state: completedSteps.has(i)
        ? 'completed'
        : currentStep === i
        ? 'active'
        : 'pending',
    }))
  }, [currentStep, completedSteps])

  // ---------------------------------------------------------------------------
  // Navigation helpers
  // ---------------------------------------------------------------------------

  const goToStep = useCallback((index: number) => {
    // AC2: only allow going back to completed steps
    if (completedSteps.has(index) || index === currentStep) {
      setCurrentStep(index)
    }
  }, [completedSteps, currentStep])

  const advanceStep = useCallback(() => {
    setCompletedSteps((prev) => new Set([...prev, currentStep]))
    setCurrentStep((prev) => prev + 1)
  }, [currentStep])

  const goBack = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1)
    }
  }, [currentStep])

  // ---------------------------------------------------------------------------
  // T7: Broadcast submit
  // ---------------------------------------------------------------------------

  const handlePublish = useCallback(async () => {
    setPublishing(true)
    setPublishError(null)

    const audiencePayload: 'all' | 'approved' | 'rejected' | string[] =
      audience === 'manual'
        ? effectiveRecipients.map((s) => s.row.studentId)
        : audience

    try {
      type BroadcastResponse = {
        portal_published: number
        whatsapp_sent: number
        failures: number
        failure_list?: Array<{ student_id: string; student_name: string; student_number: string; reason: string }>
      }

      const data = await apiFetch<BroadcastResponse>('/api/v1/broadcast/', {
        method: 'POST',
        body: JSON.stringify({
          context_id: contextId,
          audience: audiencePayload,
          channels: Array.from(channels),
          message_template: messageTemplate,
        }),
      })

      setPublishResult({
        portalPublished: data.portal_published,
        whatsappSent: data.whatsapp_sent,
        failures: data.failures,
        failureList: (data.failure_list ?? []).map((f) => ({
          studentId: f.student_id,
          studentName: f.student_name,
          studentNumber: f.student_number,
          reason: f.reason,
        })),
      })
    } catch (err) {
      // Story 8.2: surface FastAPI's sanitised error to the user — no mock
      // fallback. The dashboard disables the publish action when matched=0
      // so the network call should normally succeed.
      setPublishError(
        err instanceof Error ? err.message : 'Erro ao publicar notas.',
      )
    } finally {
      setPublishing(false)
    }
  }, [audience, channels, messageTemplate, contextId, effectiveRecipients])

  // T9: Resend for failures only
  const handleResend = useCallback(async () => {
    if (!publishResult || publishResult.failureList.length === 0) return
    setResending(true)

    const failedIds = publishResult.failureList.map((f) => f.studentId)

    try {
      type BroadcastResponse = {
        portal_published: number
        whatsapp_sent: number
        failures: number
        failure_list?: Array<{ student_id: string; student_name: string; student_number: string; reason: string }>
      }

      const data = await apiFetch<BroadcastResponse>('/api/v1/broadcast/', {
        method: 'POST',
        body: JSON.stringify({
          context_id: contextId,
          audience: failedIds,
          channels: Array.from(channels),
          message_template: messageTemplate,
        }),
      })

      setPublishResult((prev) =>
        prev
          ? {
              ...prev,
              whatsappSent: prev.whatsappSent + data.whatsapp_sent,
              failures: data.failures,
              failureList: (data.failure_list ?? []).map((f) => ({
                studentId: f.student_id,
                studentName: f.student_name,
                studentNumber: f.student_number,
                reason: f.reason,
              })),
            }
          : prev,
      )
    } catch (err) {
      setPublishError(
        err instanceof Error ? err.message : 'Erro ao reenviar notificações.',
      )
    } finally {
      setResending(false)
    }
  }, [publishResult, contextId, channels, messageTemplate])

  // Export: simple CSV download of failure list
  const handleExport = useCallback(() => {
    if (!publishResult) return
    const lines = [
      'Nome,Número,Razão',
      ...publishResult.failureList.map((f) => `${f.studentName},${f.studentNumber},${f.reason}`),
    ]
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `broadcast-relatorio-${contextId}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }, [publishResult, contextId])

  // ---------------------------------------------------------------------------
  // Channel toggle
  // ---------------------------------------------------------------------------

  const toggleChannel = useCallback((channel: ChannelType) => {
    setChannels((prev) => {
      const next = new Set(prev)
      if (next.has(channel)) {
        next.delete(channel)
      } else {
        next.add(channel)
      }
      return next
    })
  }, [])

  // ---------------------------------------------------------------------------
  // Render: result screen (post-publish, not a wizard step)
  // ---------------------------------------------------------------------------

  if (publishResult) {
    return (
      <WizardLayout>
        <BroadcastResultSummary
          result={publishResult}
          onResend={handleResend}
          onExport={handleExport}
          onBack={() => navigate('/painel')}
          resending={resending}
        />
      </WizardLayout>
    )
  }

  // ---------------------------------------------------------------------------
  // Render: loading
  // ---------------------------------------------------------------------------

  if (loading) {
    return (
      <WizardLayout>
        <div className="flex items-center justify-center py-24 text-muted-foreground">
          <span className="animate-pulse">A carregar dados…</span>
        </div>
      </WizardLayout>
    )
  }

  if (loadError || !contextItem) {
    return (
      <WizardLayout>
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg px-6 py-8 text-center">
          <p className="text-destructive font-medium mb-4">
            {loadError ?? 'Contexto académico não encontrado.'}
          </p>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="text-sm text-primary hover:underline"
          >
            ← Voltar
          </button>
        </div>
      </WizardLayout>
    )
  }

  // ---------------------------------------------------------------------------
  // Render: wizard
  // ---------------------------------------------------------------------------

  return (
    <WizardLayout>
      {/* Title */}
      <div className="mb-4">
        <h1 className="text-xl font-bold text-foreground">Publicar Notas</h1>
        <p className="text-sm text-muted-foreground mt-0.5">{breadcrumb}</p>
      </div>

      {/* AC1: PublicationStepper */}
      <PublicationStepper steps={stepStates} onStepClick={goToStep} />

      {/* Publish error */}
      {publishError && (
        <div role="alert" className="mb-4 rounded-md bg-destructive/10 border border-destructive/20 px-4 py-3 text-sm text-destructive">
          {publishError}
        </div>
      )}

      {/* ── Step 1: Revisão ──────────────────────────────────────────────── */}
      {currentStep === 0 && (
        <div className="bg-card rounded-lg border border-border p-6 flex flex-col gap-5">
          <div>
            <h2 className="text-base font-semibold text-foreground mb-0.5">① Revisão das Notas</h2>
            <p className="text-sm text-muted-foreground">{breadcrumb}</p>
          </div>

          {/* AC3: warning about incomplete students */}
          {incompleteStudents.length > 0 && (
            <div
              role="alert"
              className="bg-warning/10 border border-warning/20 rounded-md px-4 py-3 text-sm text-warning"
            >
              <strong>{incompleteStudents.length} aluno(s) com notas incompletas</strong> serão excluídos automaticamente da publicação.{' '}
              <button
                type="button"
                className="underline hover:no-underline"
                onClick={() => {
                  const el = document.getElementById('excluded-list')
                  if (el) el.scrollIntoView({ behavior: 'smooth' })
                }}
              >
                Ver lista de excluídos ↓
              </button>
            </div>
          )}

          {/* T3: Review table — complete students */}
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-2">
              Alunos com nota completa ({completeStudents.length})
            </h3>
            <div className="border border-border rounded-lg overflow-hidden">
              <table className="w-full text-sm" aria-label="Tabela de revisão de notas">
                <thead className="bg-muted/50 border-b border-border">
                  <tr>
                    <th className="text-left px-4 py-2.5 font-medium text-muted-foreground text-xs uppercase tracking-wide">Nº</th>
                    <th className="text-left px-4 py-2.5 font-medium text-muted-foreground text-xs uppercase tracking-wide">Nome</th>
                    {contextItem.components.map((c) => (
                      <th key={c.id} className="text-center px-3 py-2.5 font-medium text-muted-foreground text-xs uppercase tracking-wide">
                        {c.name}
                      </th>
                    ))}
                    <th className="text-center px-4 py-2.5 font-medium text-muted-foreground text-xs uppercase tracking-wide">Nota Final</th>
                    <th className="text-center px-4 py-2.5 font-medium text-muted-foreground text-xs uppercase tracking-wide">Resultado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {completeStudents.map(({ row, nota }) => (
                    <tr key={row.studentId} className="hover:bg-muted/50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{row.studentNumber}</td>
                      <td className="px-4 py-3 font-medium text-foreground">{row.studentName}</td>
                      {contextItem.components.map((c) => (
                        <td key={c.id} className="px-3 py-3 text-center text-foreground">
                          {row.components[c.id]?.value ?? '—'}
                        </td>
                      ))}
                      <td className="px-4 py-3 text-center font-bold text-foreground">
                        {nota !== null ? nota : '—'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <ResultBadge nota={nota} />
                      </td>
                    </tr>
                  ))}
                  {completeStudents.length === 0 && (
                    <tr>
                      <td colSpan={4 + contextItem.components.length} className="px-4 py-8 text-center text-muted-foreground text-sm">
                        Nenhum aluno com nota completa.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* AC3: Excluded students list */}
          {incompleteStudents.length > 0 && (
            <div id="excluded-list">
              <h3 className="text-sm font-semibold text-muted-foreground mb-2">
                Excluídos — notas incompletas ({incompleteStudents.length})
              </h3>
              <div className="border border-warning/30 rounded-lg overflow-hidden bg-warning/5">
                <table className="w-full text-sm" aria-label="Alunos excluídos da publicação">
                  <thead className="bg-warning/10 border-b border-warning/30">
                    <tr>
                      <th className="text-left px-4 py-2 font-medium text-warning text-xs">Nº</th>
                      <th className="text-left px-4 py-2 font-medium text-warning text-xs">Nome</th>
                      <th className="text-left px-4 py-2 font-medium text-warning text-xs">Situação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {incompleteStudents.map(({ row, badge }) => (
                      <tr key={row.studentId}>
                        <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">{row.studentNumber}</td>
                        <td className="px-4 py-2.5 text-foreground">{row.studentName}</td>
                        <td className="px-4 py-2.5">
                          <span className="text-xs bg-warning/10 text-warning px-2 py-0.5 rounded-full">
                            {badge}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* AC3+AC4: action buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted/50 transition-colors"
            >
              Cancelar
            </button>
            {/* AC4: Always active */}
            <button
              type="button"
              onClick={advanceStep}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-md bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              Avançar: Audiência →
            </button>
          </div>
        </div>
      )}

      {/* ── Step 2: Audiência ─────────────────────────────────────────────── */}
      {currentStep === 1 && (
        <div className="bg-card rounded-lg border border-border p-6 flex flex-col gap-5">
          <h2 className="text-base font-semibold text-foreground">② Seleccionar Audiência</h2>

          {/* AC5: no-phone warning */}
          {noPhoneCount > 0 && (
            <div
              role="alert"
              className="bg-warning/10 border border-warning/20 rounded-md px-4 py-3 text-sm text-warning"
            >
              <strong>{noPhoneCount} aluno(s) sem telefone válido</strong> serão excluídos automaticamente das notificações WhatsApp.
            </div>
          )}

          {/* AC5: RadioGroup */}
          <fieldset>
            <legend id="audience-legend" className="text-sm font-medium text-foreground mb-3">
              Seleccionar Audiência
            </legend>
            <RadioGroup
              role="radiogroup"
              aria-labelledby="audience-legend"
              value={audience}
              onValueChange={(v) => setAudience(v as AudienceType)}
              className="flex flex-col gap-3"
            >
              <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors has-[input:checked]:border-primary has-[input:checked]:bg-primary/5">
                <RadioGroupItem value="all" id="aud-all" aria-checked={audience === 'all'} />
                <span className="text-sm text-foreground flex-1">
                  Todos os alunos com nota completa
                </span>
                <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full font-mono">
                  {audienceCounts.all} alunos
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors has-[input:checked]:border-primary has-[input:checked]:bg-primary/5">
                <RadioGroupItem value="approved" id="aud-approved" aria-checked={audience === 'approved'} />
                <span className="text-sm text-foreground flex-1">
                  Apenas aprovados
                </span>
                <span className="text-xs bg-success/10 text-success px-2 py-0.5 rounded-full font-mono">
                  {audienceCounts.approved} alunos
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors has-[input:checked]:border-primary has-[input:checked]:bg-primary/5">
                <RadioGroupItem value="rejected" id="aud-rejected" aria-checked={audience === 'rejected'} />
                <span className="text-sm text-foreground flex-1">
                  Apenas reprovados
                </span>
                <span className="text-xs bg-destructive/10 text-destructive px-2 py-0.5 rounded-full font-mono">
                  {audienceCounts.rejected} alunos
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors has-[input:checked]:border-primary has-[input:checked]:bg-primary/5">
                <RadioGroupItem value="manual" id="aud-manual" aria-checked={audience === 'manual'} />
                <span className="text-sm text-foreground flex-1">
                  Selecção manual
                </span>
                <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full font-mono">
                  {audienceCounts.all} alunos
                </span>
              </label>
            </RadioGroup>
          </fieldset>

          {/* Action buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={goBack}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted/50 transition-colors"
            >
              ← Revisão
            </button>
            <button
              type="button"
              onClick={advanceStep}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-md bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              Avançar: Canais →
            </button>
          </div>
        </div>
      )}

      {/* ── Step 3: Canais ────────────────────────────────────────────────── */}
      {currentStep === 2 && (
        <div className="bg-card rounded-lg border border-border p-6 flex flex-col gap-5">
          <h2 className="text-base font-semibold text-foreground">③ Canais de Notificação</h2>

          {/* AC13: WhatsApp disconnected warning */}
          {!waStatus.connected && (
            <div
              role="alert"
              className="bg-destructive/10 border border-destructive/20 rounded-md px-4 py-3 text-sm text-destructive"
            >
              <strong>WhatsApp desconectado.</strong> Para enviar por WhatsApp, conecte primeiro no{' '}
              <button
                type="button"
                onClick={() => navigate('/painel')}
                className="underline hover:no-underline font-medium"
              >
                Painel (Passo 4)
              </button>.
            </div>
          )}

          {/* AC6: Channel checkboxes */}
          <div className="flex flex-col gap-3">
            <h3 className="text-sm font-medium text-foreground">Seleccionar canais</h3>

            {/* WhatsApp */}
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors">
              <Checkbox
                id="ch-whatsapp"
                checked={channels.has('whatsapp')}
                onCheckedChange={() => toggleChannel('whatsapp')}
                disabled={!waStatus.connected}
                aria-disabled={!waStatus.connected}
              />
              <span className="text-sm text-foreground flex-1">
                WhatsApp
              </span>
              <div className="flex items-center gap-2">
                {waChecking ? (
                  <span className="text-xs text-muted-foreground">A verificar…</span>
                ) : (
                  <span
                    className={[
                      'text-xs px-2 py-0.5 rounded-full font-medium',
                      waStatus.connected
                        ? 'bg-success/10 text-success'
                        : 'bg-destructive/10 text-destructive',
                    ].join(' ')}
                  >
                    {waStatus.connected ? '● Conectado' : '● Desconectado'}
                  </span>
                )}
                <span className="text-xs text-muted-foreground font-mono">
                  {effectiveRecipients.length} destinatários
                </span>
              </div>
            </label>

            {/* Email — not configured */}
            <label className="flex items-center gap-3 cursor-not-allowed p-3 rounded-lg border border-border bg-muted/50 opacity-50">
              <Checkbox id="ch-email" checked={false} disabled aria-disabled="true" />
              <span className="text-sm text-muted-foreground flex-1">Email</span>
              <span className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded-full">
                Não configurado
              </span>
            </label>

            {/* Portal only */}
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors">
              <Checkbox
                id="ch-portal"
                checked={channels.has('portal_only')}
                onCheckedChange={() => toggleChannel('portal_only')}
              />
              <span className="text-sm text-foreground flex-1">Apenas Portal (sem notificação)</span>
            </label>
          </div>

          {/* AC6: Message template + live preview */}
          <div className="flex flex-col gap-3">
            <div>
              <label htmlFor="message-template" className="text-sm font-medium text-foreground block mb-1.5">
                Template da mensagem WhatsApp
              </label>
              <textarea
                id="message-template"
                value={messageTemplate}
                onChange={(e) => setMessageTemplate(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-border bg-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/30 focus:border-primary resize-none"
                placeholder="Olá {{nome}}! A sua nota é {{nota_final}}."
              />
              <p className="text-xs text-muted-foreground mt-1">
                Variáveis: <code className="bg-muted px-1 rounded">{'{{nome}}'}</code>{' '}
                <code className="bg-muted px-1 rounded">{'{{disciplina}}'}</code>{' '}
                <code className="bg-muted px-1 rounded">{'{{semestre}}'}</code>{' '}
                <code className="bg-muted px-1 rounded">{'{{nota_final}}'}</code>{' '}
                <code className="bg-muted px-1 rounded">{'{{resultado}}'}</code>
              </p>
            </div>

            {/* Live preview */}
            {completeStudents.length > 0 && (
              <div className="bg-muted/50 border border-border rounded-lg p-3">
                <p className="text-xs font-medium text-muted-foreground mb-1.5 uppercase tracking-wide">
                  Pré-visualização (1.º aluno)
                </p>
                <p className="text-sm text-foreground whitespace-pre-wrap">{previewText}</p>
              </div>
            )}
          </div>

          {/* AC7: Avançar disabled until ≥1 channel selected */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={goBack}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted/50 transition-colors"
            >
              ← Audiência
            </button>
            <button
              type="button"
              onClick={advanceStep}
              disabled={channels.size === 0}
              aria-disabled={channels.size === 0}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-md bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Avançar: Confirmar →
            </button>
          </div>
        </div>
      )}

      {/* ── Step 4: Confirmar ─────────────────────────────────────────────── */}
      {currentStep === 3 && (
        <div className="bg-card rounded-lg border border-border p-6 flex flex-col gap-5">
          <h2 className="text-base font-semibold text-foreground">④ Confirmar Publicação</h2>

          {/* AC8: Summary box */}
          <div className="bg-muted/50 border border-border rounded-lg p-4 flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Contexto</span>
              <span className="font-medium text-foreground text-right max-w-[60%]">{breadcrumb}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Audiência</span>
              <span className="font-medium text-foreground">
                {audience === 'all' && `Todos (${audienceCounts.all} alunos)`}
                {audience === 'approved' && `Apenas aprovados (${audienceCounts.approved} alunos)`}
                {audience === 'rejected' && `Apenas reprovados (${audienceCounts.rejected} alunos)`}
                {audience === 'manual' && `Selecção manual (${audienceCounts.all} alunos)`}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Excluídos</span>
              <span className="font-medium text-foreground">
                {incompleteStudents.length} incompletos{noPhoneCount > 0 ? ` + ${noPhoneCount} sem telefone` : ''}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Canais</span>
              <span className="font-medium text-foreground">
                {Array.from(channels).join(', ') || '—'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Destinatários efectivos</span>
              <span className="font-semibold text-foreground">{effectiveRecipients.length} alunos</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Portal</span>
              <span className="font-medium text-success flex items-center gap-1"><CheckCircle className="size-3.5" /> Visível após publicação</span>
            </div>
          </div>

          {/* AC8: Amber warning */}
          <div
            role="alert"
            className="bg-warning/10 border border-warning/20 rounded-lg px-4 py-3 text-sm text-warning flex items-start gap-2"
          >
            <AlertTriangle className="size-4 shrink-0 mt-0.5" />
            <span><strong>Atenção:</strong> Esta acção é irreversível. As notas ficarão visíveis no portal para os estudantes e as notificações WhatsApp serão enviadas imediatamente. Certifique-se de que todas as notas estão correctas.</span>
          </div>

          {/* AC8: Mandatory confirmation checkbox */}
          <div className="flex items-start gap-3">
            <Checkbox
              id="confirm-checkbox"
              checked={confirmChecked}
              onCheckedChange={(checked) => setConfirmChecked(checked === true)}
              className="mt-0.5"
            />
            <label htmlFor="confirm-checkbox" className="text-sm text-foreground cursor-pointer leading-relaxed">
              Confirmo que revi as notas e autorizo a publicação.
            </label>
          </div>

          {/* AC9: Action buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={goBack}
              disabled={publishing}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted transition-colors disabled:opacity-50"
            >
              <ChevronLeft className="size-4" /> Canais
            </button>

            {/* AC8: Disabled until checkbox checked; AC9: loading state */}
            <button
              type="button"
              onClick={handlePublish}
              disabled={!confirmChecked || publishing}
              aria-disabled={!confirmChecked || publishing}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {publishing ? (
                <>
                  <RefreshCw className="size-4 animate-spin" />
                  A publicar…
                </>
              ) : (
                <><Rocket className="size-4" /> Publicar e Enviar Notificações</>
              )}
            </button>
          </div>
        </div>
      )}
    </WizardLayout>
  )
}
