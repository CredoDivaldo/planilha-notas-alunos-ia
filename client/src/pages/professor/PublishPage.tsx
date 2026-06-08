// PublishPage — /publicar — 4-step publication wizard (Story 7.7)
// AC1-AC14: stepper, audience, channels, confirm, result screen, WhatsApp status, accessibility

import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
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
// Mock data — fallback when API unavailable
// ---------------------------------------------------------------------------

const MOCK_CONTEXT: ContextItem = {
  id: 'ctx-mock-1',
  turma: 'ING-T1',
  disciplina: 'Inglês Técnico',
  semestre: '2026/1',
  turno: 'Manhã',
  alunosCount: 6,
  delegado: null,
  components: [
    { id: 'c1', name: 'Frequência', weight: 40 },
    { id: 'c2', name: 'Mini-teste', weight: 30 },
    { id: 'c3', name: 'Exame', weight: 30 },
  ],
}

const MOCK_ROWS: StudentRow[] = [
  {
    studentId: 'st-1', studentNumber: '2024001', studentName: 'Ana Silva', published: false,
    components: { c1: { gradeId: 'g-1', value: 16 }, c2: { gradeId: 'g-2', value: 14 }, c3: { gradeId: 'g-3', value: 15 } },
  },
  {
    studentId: 'st-2', studentNumber: '2024002', studentName: 'Bruno Costa', published: false,
    components: { c1: { gradeId: 'g-4', value: 12 }, c2: { gradeId: 'g-5', value: null }, c3: { gradeId: 'g-6', value: 11 } },
  },
  {
    studentId: 'st-3', studentNumber: '2024003', studentName: 'Carla Mendes', published: true,
    components: { c1: { gradeId: 'g-7', value: 18 }, c2: { gradeId: 'g-8', value: 17 }, c3: { gradeId: 'g-9', value: 19 } },
  },
  {
    studentId: 'st-4', studentNumber: '2024004', studentName: 'David Pinto', published: false,
    components: { c1: { gradeId: 'g-10', value: 8 }, c2: { gradeId: 'g-11', value: 7 }, c3: { gradeId: 'g-12', value: 9 } },
  },
  {
    studentId: 'st-5', studentNumber: '2024005', studentName: 'Eva Rodrigues', published: false,
    components: { c1: { gradeId: 'g-13', value: null }, c2: { gradeId: 'g-14', value: null }, c3: { gradeId: 'g-15', value: null } },
  },
  {
    studentId: 'st-6', studentNumber: '2024006', studentName: 'Filipe Santos', published: false,
    components: { c1: { gradeId: 'g-16', value: 14 }, c2: { gradeId: 'g-17', value: 13 }, c3: { gradeId: 'g-18', value: null } },
  },
]

// Mock: 2 students have no valid phone (Eva, Bruno)
const MOCK_NO_PHONE_IDS = new Set(['st-2', 'st-5'])

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
  if (nota === null) return <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">Incompleta</span>
  if (nota >= 10) return <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">Aprovado ✓</span>
  return <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Reprovado ✗</span>
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

  // T10: context propagation via ?context={id}
  const contextId = searchParams.get('context') ?? sessionStorage.getItem('active_context_id') ?? MOCK_CONTEXT.id

  // Data
  const [contextItem, setContextItem] = useState<ContextItem>(MOCK_CONTEXT)
  const [rows, setRows] = useState<StudentRow[]>(MOCK_ROWS)
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
    try {
      const ctx = await apiFetch<ContextItem>(`/academic-contexts/${contextId}`)
      setContextItem(ctx)
      const gradesData = await apiFetch<{ students: StudentRow[] }>(`/grades/?context_id=${contextId}`)
      setRows(gradesData.students ?? MOCK_ROWS)
    } catch {
      setContextItem(MOCK_CONTEXT)
      setRows(MOCK_ROWS)
    } finally {
      setLoading(false)
    }
  }, [contextId])

  useState(() => { loadData() })

  // T11: WhatsApp status polling
  const checkWaStatus = useCallback(async () => {
    setWaChecking(true)
    try {
      const data = await apiFetch<{ connected: boolean; instance_name: string }>('/whatsapp/status')
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
      const nota = calcNotaFinal(row.components, contextItem.components)
      const badge = getRowBadgeLabel(row.components, contextItem.components, row.published)
      const complete = badge !== 'Incompleta' && badge !== 'Vazio'
      const hasPhone = !MOCK_NO_PHONE_IDS.has(row.studentId)
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
    if (!first) return messageTemplate
    return renderPreview(messageTemplate, first, contextItem.disciplina, contextItem.semestre)
  }, [messageTemplate, completeStudents, contextItem.disciplina, contextItem.semestre])

  const breadcrumb = `${contextItem.turma} · ${contextItem.disciplina} · ${contextItem.semestre} · ${contextItem.turno}`

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

      const data = await apiFetch<BroadcastResponse>('/broadcast/', {
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

      const data = await apiFetch<BroadcastResponse>('/broadcast/', {
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
        <div className="flex items-center justify-center py-24 text-slate-500">
          <span className="animate-pulse">A carregar dados…</span>
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
        <h1 className="text-xl font-bold text-slate-900">Publicar Notas</h1>
        <p className="text-sm text-slate-500 mt-0.5">{breadcrumb}</p>
      </div>

      {/* AC1: PublicationStepper */}
      <PublicationStepper steps={stepStates} onStepClick={goToStep} />

      {/* Publish error */}
      {publishError && (
        <div role="alert" className="mb-4 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-[#B91C1C]">
          {publishError}
        </div>
      )}

      {/* ── Step 1: Revisão ──────────────────────────────────────────────── */}
      {currentStep === 0 && (
        <div className="bg-white rounded-lg border border-slate-200 p-6 flex flex-col gap-5">
          <div>
            <h2 className="text-base font-semibold text-slate-900 mb-0.5">① Revisão das Notas</h2>
            <p className="text-sm text-slate-500">{breadcrumb}</p>
          </div>

          {/* AC3: warning about incomplete students */}
          {incompleteStudents.length > 0 && (
            <div
              role="alert"
              className="bg-amber-50 border border-amber-200 rounded-md px-4 py-3 text-sm text-[#B45309]"
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
            <h3 className="text-sm font-semibold text-slate-700 mb-2">
              Alunos com nota completa ({completeStudents.length})
            </h3>
            <div className="border border-slate-200 rounded-lg overflow-hidden">
              <table className="w-full text-sm" aria-label="Tabela de revisão de notas">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="text-left px-4 py-2.5 font-medium text-slate-600 text-xs uppercase tracking-wide">Nº</th>
                    <th className="text-left px-4 py-2.5 font-medium text-slate-600 text-xs uppercase tracking-wide">Nome</th>
                    {contextItem.components.map((c) => (
                      <th key={c.id} className="text-center px-3 py-2.5 font-medium text-slate-600 text-xs uppercase tracking-wide">
                        {c.name}
                      </th>
                    ))}
                    <th className="text-center px-4 py-2.5 font-medium text-slate-600 text-xs uppercase tracking-wide">Nota Final</th>
                    <th className="text-center px-4 py-2.5 font-medium text-slate-600 text-xs uppercase tracking-wide">Resultado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {completeStudents.map(({ row, nota }) => (
                    <tr key={row.studentId} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{row.studentNumber}</td>
                      <td className="px-4 py-3 font-medium text-slate-900">{row.studentName}</td>
                      {contextItem.components.map((c) => (
                        <td key={c.id} className="px-3 py-3 text-center text-slate-700">
                          {row.components[c.id]?.value ?? '—'}
                        </td>
                      ))}
                      <td className="px-4 py-3 text-center font-bold text-slate-900">
                        {nota !== null ? nota : '—'}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <ResultBadge nota={nota} />
                      </td>
                    </tr>
                  ))}
                  {completeStudents.length === 0 && (
                    <tr>
                      <td colSpan={4 + contextItem.components.length} className="px-4 py-8 text-center text-slate-400 text-sm">
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
              <h3 className="text-sm font-semibold text-slate-500 mb-2">
                Excluídos — notas incompletas ({incompleteStudents.length})
              </h3>
              <div className="border border-amber-200 rounded-lg overflow-hidden bg-amber-50/30">
                <table className="w-full text-sm" aria-label="Alunos excluídos da publicação">
                  <thead className="bg-amber-50 border-b border-amber-200">
                    <tr>
                      <th className="text-left px-4 py-2 font-medium text-amber-700 text-xs">Nº</th>
                      <th className="text-left px-4 py-2 font-medium text-amber-700 text-xs">Nome</th>
                      <th className="text-left px-4 py-2 font-medium text-amber-700 text-xs">Situação</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-amber-100">
                    {incompleteStudents.map(({ row, badge }) => (
                      <tr key={row.studentId}>
                        <td className="px-4 py-2.5 font-mono text-xs text-slate-500">{row.studentNumber}</td>
                        <td className="px-4 py-2.5 text-slate-700">{row.studentName}</td>
                        <td className="px-4 py-2.5">
                          <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
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
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-slate-300 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Cancelar
            </button>
            {/* AC4: Always active */}
            <button
              type="button"
              onClick={advanceStep}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-md bg-[#0D6EFD] text-white text-sm font-medium hover:bg-[#0D6EFD]/90 transition-colors"
            >
              Avançar: Audiência →
            </button>
          </div>
        </div>
      )}

      {/* ── Step 2: Audiência ─────────────────────────────────────────────── */}
      {currentStep === 1 && (
        <div className="bg-white rounded-lg border border-slate-200 p-6 flex flex-col gap-5">
          <h2 className="text-base font-semibold text-slate-900">② Seleccionar Audiência</h2>

          {/* AC5: no-phone warning */}
          {noPhoneCount > 0 && (
            <div
              role="alert"
              className="bg-amber-50 border border-amber-200 rounded-md px-4 py-3 text-sm text-[#B45309]"
            >
              <strong>{noPhoneCount} aluno(s) sem telefone válido</strong> serão excluídos automaticamente das notificações WhatsApp.
            </div>
          )}

          {/* AC5: RadioGroup */}
          <fieldset>
            <legend id="audience-legend" className="text-sm font-medium text-slate-700 mb-3">
              Seleccionar Audiência
            </legend>
            <RadioGroup
              role="radiogroup"
              aria-labelledby="audience-legend"
              value={audience}
              onValueChange={(v) => setAudience(v as AudienceType)}
              className="flex flex-col gap-3"
            >
              <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors has-[input:checked]:border-[#0D6EFD] has-[input:checked]:bg-blue-50/30">
                <RadioGroupItem value="all" id="aud-all" aria-checked={audience === 'all'} />
                <span className="text-sm text-slate-800 flex-1">
                  Todos os alunos com nota completa
                </span>
                <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full font-mono">
                  {audienceCounts.all} alunos
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors has-[input:checked]:border-[#0D6EFD] has-[input:checked]:bg-blue-50/30">
                <RadioGroupItem value="approved" id="aud-approved" aria-checked={audience === 'approved'} />
                <span className="text-sm text-slate-800 flex-1">
                  Apenas aprovados
                </span>
                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-mono">
                  {audienceCounts.approved} alunos
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors has-[input:checked]:border-[#0D6EFD] has-[input:checked]:bg-blue-50/30">
                <RadioGroupItem value="rejected" id="aud-rejected" aria-checked={audience === 'rejected'} />
                <span className="text-sm text-slate-800 flex-1">
                  Apenas reprovados
                </span>
                <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-mono">
                  {audienceCounts.rejected} alunos
                </span>
              </label>

              <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors has-[input:checked]:border-[#0D6EFD] has-[input:checked]:bg-blue-50/30">
                <RadioGroupItem value="manual" id="aud-manual" aria-checked={audience === 'manual'} />
                <span className="text-sm text-slate-800 flex-1">
                  Selecção manual
                </span>
                <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded-full font-mono">
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
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-slate-300 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              ← Revisão
            </button>
            <button
              type="button"
              onClick={advanceStep}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-md bg-[#0D6EFD] text-white text-sm font-medium hover:bg-[#0D6EFD]/90 transition-colors"
            >
              Avançar: Canais →
            </button>
          </div>
        </div>
      )}

      {/* ── Step 3: Canais ────────────────────────────────────────────────── */}
      {currentStep === 2 && (
        <div className="bg-white rounded-lg border border-slate-200 p-6 flex flex-col gap-5">
          <h2 className="text-base font-semibold text-slate-900">③ Canais de Notificação</h2>

          {/* AC13: WhatsApp disconnected warning */}
          {!waStatus.connected && (
            <div
              role="alert"
              className="bg-red-50 border border-red-200 rounded-md px-4 py-3 text-sm text-[#B91C1C]"
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
            <h3 className="text-sm font-medium text-slate-700">Seleccionar canais</h3>

            {/* WhatsApp */}
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">
              <Checkbox
                id="ch-whatsapp"
                checked={channels.has('whatsapp')}
                onCheckedChange={() => toggleChannel('whatsapp')}
                disabled={!waStatus.connected}
                aria-disabled={!waStatus.connected}
              />
              <span className="text-sm text-slate-800 flex-1">
                WhatsApp
              </span>
              <div className="flex items-center gap-2">
                {waChecking ? (
                  <span className="text-xs text-slate-400">A verificar…</span>
                ) : (
                  <span
                    className={[
                      'text-xs px-2 py-0.5 rounded-full font-medium',
                      waStatus.connected
                        ? 'bg-green-100 text-green-700'
                        : 'bg-red-100 text-red-700',
                    ].join(' ')}
                  >
                    {waStatus.connected ? '● Conectado' : '● Desconectado'}
                  </span>
                )}
                <span className="text-xs text-slate-500 font-mono">
                  {effectiveRecipients.length} destinatários
                </span>
              </div>
            </label>

            {/* Email — not configured */}
            <label className="flex items-center gap-3 cursor-not-allowed p-3 rounded-lg border border-slate-200 bg-slate-50 opacity-50">
              <Checkbox id="ch-email" checked={false} disabled aria-disabled="true" />
              <span className="text-sm text-slate-600 flex-1">Email</span>
              <span className="text-xs bg-slate-200 text-slate-500 px-2 py-0.5 rounded-full">
                Não configurado
              </span>
            </label>

            {/* Portal only */}
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">
              <Checkbox
                id="ch-portal"
                checked={channels.has('portal_only')}
                onCheckedChange={() => toggleChannel('portal_only')}
              />
              <span className="text-sm text-slate-800 flex-1">Apenas Portal (sem notificação)</span>
            </label>
          </div>

          {/* AC6: Message template + live preview */}
          <div className="flex flex-col gap-3">
            <div>
              <label htmlFor="message-template" className="text-sm font-medium text-slate-700 block mb-1.5">
                Template da mensagem WhatsApp
              </label>
              <textarea
                id="message-template"
                value={messageTemplate}
                onChange={(e) => setMessageTemplate(e.target.value)}
                rows={3}
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0D6EFD]/30 focus:border-[#0D6EFD] resize-none"
                placeholder="Olá {{nome}}! A sua nota é {{nota_final}}."
              />
              <p className="text-xs text-slate-400 mt-1">
                Variáveis: <code className="bg-slate-100 px-1 rounded">{'{{nome}}'}</code>{' '}
                <code className="bg-slate-100 px-1 rounded">{'{{disciplina}}'}</code>{' '}
                <code className="bg-slate-100 px-1 rounded">{'{{semestre}}'}</code>{' '}
                <code className="bg-slate-100 px-1 rounded">{'{{nota_final}}'}</code>{' '}
                <code className="bg-slate-100 px-1 rounded">{'{{resultado}}'}</code>
              </p>
            </div>

            {/* Live preview */}
            {completeStudents.length > 0 && (
              <div className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                <p className="text-xs font-medium text-slate-500 mb-1.5 uppercase tracking-wide">
                  Pré-visualização (1.º aluno)
                </p>
                <p className="text-sm text-slate-800 whitespace-pre-wrap">{previewText}</p>
              </div>
            )}
          </div>

          {/* AC7: Avançar disabled until ≥1 channel selected */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={goBack}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-slate-300 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
            >
              ← Audiência
            </button>
            <button
              type="button"
              onClick={advanceStep}
              disabled={channels.size === 0}
              aria-disabled={channels.size === 0}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-md bg-[#0D6EFD] text-white text-sm font-medium hover:bg-[#0D6EFD]/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Avançar: Confirmar →
            </button>
          </div>
        </div>
      )}

      {/* ── Step 4: Confirmar ─────────────────────────────────────────────── */}
      {currentStep === 3 && (
        <div className="bg-white rounded-lg border border-slate-200 p-6 flex flex-col gap-5">
          <h2 className="text-base font-semibold text-slate-900">④ Confirmar Publicação</h2>

          {/* AC8: Summary box */}
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Contexto</span>
              <span className="font-medium text-slate-800 text-right max-w-[60%]">{breadcrumb}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Audiência</span>
              <span className="font-medium text-slate-800">
                {audience === 'all' && `Todos (${audienceCounts.all} alunos)`}
                {audience === 'approved' && `Apenas aprovados (${audienceCounts.approved} alunos)`}
                {audience === 'rejected' && `Apenas reprovados (${audienceCounts.rejected} alunos)`}
                {audience === 'manual' && `Selecção manual (${audienceCounts.all} alunos)`}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Excluídos</span>
              <span className="font-medium text-slate-700">
                {incompleteStudents.length} incompletos{noPhoneCount > 0 ? ` + ${noPhoneCount} sem telefone` : ''}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Canais</span>
              <span className="font-medium text-slate-800">
                {Array.from(channels).join(', ') || '—'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Destinatários efectivos</span>
              <span className="font-semibold text-slate-900">{effectiveRecipients.length} alunos</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Portal</span>
              <span className="font-medium text-[#15803D]">✓ Visível após publicação</span>
            </div>
          </div>

          {/* AC8: Amber warning */}
          <div
            role="alert"
            className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-[#B45309]"
          >
            <strong>⚠️ Atenção:</strong> Esta acção é irreversível. As notas ficarão visíveis no portal para os estudantes e as notificações WhatsApp serão enviadas imediatamente. Certifique-se de que todas as notas estão correctas.
          </div>

          {/* AC8: Mandatory confirmation checkbox */}
          <div className="flex items-start gap-3">
            <Checkbox
              id="confirm-checkbox"
              checked={confirmChecked}
              onCheckedChange={(checked) => setConfirmChecked(checked === true)}
              className="mt-0.5"
            />
            <label htmlFor="confirm-checkbox" className="text-sm text-slate-700 cursor-pointer leading-relaxed">
              Confirmo que revi as notas e autorizo a publicação.
            </label>
          </div>

          {/* AC9: Action buttons */}
          <div className="flex items-center justify-between pt-2">
            <button
              type="button"
              onClick={goBack}
              disabled={publishing}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-md border border-slate-300 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              ← Canais
            </button>

            {/* AC8: Disabled until checkbox checked; AC9: loading state */}
            <button
              type="button"
              onClick={handlePublish}
              disabled={!confirmChecked || publishing}
              aria-disabled={!confirmChecked || publishing}
              className="inline-flex items-center gap-2 px-5 py-2 rounded-md bg-[#0D6EFD] text-white text-sm font-medium hover:bg-[#0D6EFD]/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {publishing ? (
                <>
                  <span className="animate-spin text-xs">⏳</span>
                  A publicar…
                </>
              ) : (
                '🚀 Publicar e Enviar Notificações'
              )}
            </button>
          </div>
        </div>
      )}
    </WizardLayout>
  )
}
