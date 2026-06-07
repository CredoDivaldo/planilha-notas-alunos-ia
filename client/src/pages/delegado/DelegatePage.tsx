import { useEffect, useState } from 'react'
import { DelegateHeader } from '@/components/organisms/DelegateHeader'
import { DelegateGradeTable } from '@/components/organisms/DelegateGradeTable'
import type { DelegateStudent } from '@/components/organisms/DelegateGradeTable'
import { StatCard } from '@/components/molecules/StatCard'
import { SearchBar } from '@/components/molecules/SearchBar'
import { Button } from '@/components/ui/button'
import { apiFetch } from '@/lib/api'
import { downloadCSV } from '@/utils/csv'

// ─── Types ────────────────────────────────────────────────────────────────────

interface SystemStatus {
  whatsappConnected: boolean
  lastBroadcast: string | null
  notesPublished: boolean
}

// ─── Mock data ────────────────────────────────────────────────────────────────

const MOCK_STUDENTS: DelegateStudent[] = [
  { id: '1', studentNumber: '2024001', name: 'Ana Silva', subject: 'Inglês', grade: 14, published: true, result: 'aprovado', contactStatus: 'ok', phone: '+244911000001' },
  { id: '2', studentNumber: '2024002', name: 'Bruno Costa', subject: 'Inglês', grade: 8, published: true, result: 'reprovado', contactStatus: 'ok', phone: '+244911000002' },
  { id: '3', studentNumber: '2024003', name: 'Carla Mendes', subject: 'Inglês', grade: null, published: false, result: 'pendente', contactStatus: 'missing' },
  { id: '4', studentNumber: '2024004', name: 'David Neto', subject: 'Inglês', grade: 16, published: true, result: 'aprovado', contactStatus: 'ok', phone: '+244911000004' },
  { id: '5', studentNumber: '2024005', name: 'Eva Rodrigues', subject: 'Inglês', grade: null, published: false, result: 'pendente', contactStatus: 'invalid', phone: '123' },
  { id: '6', studentNumber: '2024006', name: 'Fátima Sousa', subject: 'Inglês', grade: 12, published: true, result: 'aprovado', contactStatus: 'ok', phone: '+244911000006' },
  { id: '7', studentNumber: '2024007', name: 'Gabriel Lima', subject: 'Inglês', grade: 10, published: true, result: 'aprovado', contactStatus: 'ok', phone: '+244911000007' },
  { id: '8', studentNumber: '2024008', name: 'Helena Ferreira', subject: 'Inglês', grade: 7, published: true, result: 'reprovado', contactStatus: 'ok', phone: '+244911000008' },
  { id: '9', studentNumber: '2024009', name: 'Igor Santos', subject: 'Inglês', grade: null, published: false, result: 'pendente', contactStatus: 'missing' },
  { id: '10', studentNumber: '2024010', name: 'Joana Pereira', subject: 'Inglês', grade: 18, published: true, result: 'aprovado', contactStatus: 'ok', phone: '+244911000010' },
  { id: '11', studentNumber: '2024011', name: 'Kevin Alves', subject: 'Inglês', grade: 11, published: true, result: 'aprovado', contactStatus: 'ok', phone: '+244911000011' },
]

const MOCK_STATUS: SystemStatus = {
  whatsappConnected: true,
  lastBroadcast: '2026-06-06T14:30:00Z',
  notesPublished: true,
}

// ─── Contact problem panel ────────────────────────────────────────────────────

function ContactProblemsPanel({ students }: { students: DelegateStudent[] }) {
  const problematic = students.filter(
    (s) => s.contactStatus === 'invalid' || s.contactStatus === 'missing',
  )

  return (
    <section
      className="bg-white rounded-lg border border-slate-200 p-4"
      aria-labelledby="contact-problems-heading"
    >
      <h2
        id="contact-problems-heading"
        className="font-semibold text-slate-800 text-sm mb-3"
      >
        ⚠️ Contactos com Problema
      </h2>

      {problematic.length === 0 ? (
        <p className="text-sm text-[#15803D]">✅ Todos os contactos estão OK.</p>
      ) : (
        <ul className="space-y-2 mb-3">
          {problematic.map((s) => (
            <li key={s.id} className="flex items-start gap-2 text-sm">
              <span className="text-[#B45309] font-mono">{s.studentNumber}</span>
              <span className="text-slate-700 flex-1">{s.name}</span>
              <span className="text-[#B91C1C] text-xs font-medium">
                {s.contactStatus === 'missing' ? 'Sem telefone' : 'Número inválido'}
              </span>
            </li>
          ))}
        </ul>
      )}

      <p className="text-xs text-[#475569] bg-blue-50 border border-blue-100 rounded px-3 py-2">
        ℹ️ Comunique ao professor para corrigir estes contactos.
      </p>
    </section>
  )
}

// ─── System status panel ──────────────────────────────────────────────────────

function SystemStatusPanel({ status }: { status: SystemStatus }) {
  const broadcastDisplay = status.lastBroadcast
    ? new Date(status.lastBroadcast).toLocaleString('pt-PT', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Nunca'

  return (
    <section
      className="bg-white rounded-lg border border-slate-200 p-4"
      aria-labelledby="system-status-heading"
    >
      <h2
        id="system-status-heading"
        className="font-semibold text-slate-800 text-sm mb-3"
      >
        🖥️ Estado do Sistema
      </h2>

      <dl className="space-y-2 text-sm">
        <div className="flex items-center justify-between">
          <dt className="text-slate-600">WhatsApp</dt>
          <dd>
            {status.whatsappConnected ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-[#DCFCE7] text-[#15803D]">
                ✅ Conectado
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-[#FEE2E2] text-[#B91C1C]">
                ❌ Desconectado
              </span>
            )}
          </dd>
        </div>

        <div className="flex items-center justify-between">
          <dt className="text-slate-600">Último broadcast</dt>
          <dd className="text-slate-700 text-xs tabular-nums">{broadcastDisplay}</dd>
        </div>

        <div className="flex items-center justify-between">
          <dt className="text-slate-600">Notas publicadas</dt>
          <dd>
            <span
              className={`text-xs font-medium ${status.notesPublished ? 'text-[#15803D]' : 'text-[#B91C1C]'}`}
            >
              {status.notesPublished ? 'Sim' : 'Não'}
            </span>
          </dd>
        </div>
      </dl>

      <div className="mt-3 bg-slate-50 border border-slate-200 rounded px-3 py-2 flex items-start gap-2">
        <span aria-hidden="true">🔒</span>
        <p className="text-xs text-slate-600">
          Edição de notas: bloqueada (acção exclusiva do professor)
        </p>
      </div>
    </section>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function DelegatePage() {
  const [students, setStudents] = useState<DelegateStudent[]>([])
  const [systemStatus, setSystemStatus] = useState<SystemStatus>(MOCK_STATUS)
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [loading, setLoading] = useState(true)

  // ─── Fetch students (T2) ─────────────────────────────────────────────────

  useEffect(() => {
    let cancelled = false

    async function fetchStudents() {
      try {
        const data = await apiFetch<DelegateStudent[]>('/api/v1/delegado/students')
        if (!cancelled) setStudents(data)
      } catch {
        // Mock fallback — API unavailable
        if (!cancelled) setStudents(MOCK_STUDENTS)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void fetchStudents()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function fetchStatus() {
      try {
        const data = await apiFetch<SystemStatus>('/api/v1/delegado/system-status')
        if (!cancelled) setSystemStatus(data)
      } catch {
        // Mock fallback
        if (!cancelled) setSystemStatus(MOCK_STATUS)
      }
    }

    void fetchStatus()
    return () => { cancelled = true }
  }, [])

  // ─── Client-side filter (T6) ─────────────────────────────────────────────

  const filteredStudents = students.filter((s) => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) return true
    return (
      s.name.toLowerCase().includes(q) ||
      s.studentNumber.toLowerCase().includes(q)
    )
  })

  // Reset to page 1 when the search query changes (kept in handler, not effect)
  const handleSearchChange = (value: string) => {
    setCurrentPage(1)
    setSearchQuery(value)
  }

  // ─── Derived stats (T4) ──────────────────────────────────────────────────

  const totalStudents = students.length
  const publishedCount = students.filter((s) => s.published && s.grade !== null).length
  const pendingCount = students.filter((s) => !s.published || s.grade === null).length
  const noContactCount = students.filter(
    (s) => s.contactStatus === 'invalid' || s.contactStatus === 'missing',
  ).length

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      {/* Header — T3 / AC2 */}
      <DelegateHeader turma="ING-T1" semester="2026/1" />

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">

        {/* StatCards — T4 / AC3 */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard icon="👥" label="Estudantes" value={totalStudents} />
          <StatCard icon="✅" label="Notas publicadas" value={publishedCount} />
          <StatCard icon="⏳" label="Pendentes" value={pendingCount} />
          <StatCard icon="⚠️" label="Sem contacto" value={noContactCount} />
        </div>

        {/* Search + Export — T6 / T7 / AC6 / AC7 */}
        <div className="flex items-center gap-3 flex-wrap">
          <SearchBar
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Pesquisar por nome ou número…"
            className="flex-1 min-w-[200px]"
          />
          <Button
            variant="outline"
            size="sm"
            onClick={() => downloadCSV(filteredStudents)}
            className="text-[#0D6EFD] border-[#0D6EFD] hover:bg-[#0D6EFD]/5"
          >
            Exportar CSV ▾
          </Button>
        </div>

        {/* Main table — T5 / AC4 / AC5 / AC8 */}
        {loading ? (
          <div className="flex items-center justify-center py-16 text-slate-500 text-sm">
            ⏳ A carregar dados da turma…
          </div>
        ) : (
          <DelegateGradeTable
            students={filteredStudents}
            turma="ING-T1"
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
        )}

        {/* Bottom panels — T8 / T9 / AC9 / AC10 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ContactProblemsPanel students={students} />
          <SystemStatusPanel status={systemStatus} />
        </div>
      </main>
    </div>
  )
}
