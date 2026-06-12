// PortalPage — Student Portal (Story 7.6, Tela 03)
// AC1–AC13: route /portal, role=estudante guard, grades, calendar, WhatsApp banner, PDF

import { Download } from 'lucide-react'
import { useState, useCallback } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/contexts/AuthContext'
import { apiFetch } from '@/lib/api'
import { StudentPortalLayout } from '@/layouts/StudentPortalLayout'
import { StudentGradeCard } from '@/components/organisms/StudentGradeCard'
import { MonthCalendar } from '@/components/organisms/MonthCalendar'
import { UpcomingEventsList } from '@/components/organisms/UpcomingEventsList'
import type { StudentSubjectGrade } from '@/components/organisms/StudentGradeCard'
import type { CalendarEvent } from '@/components/molecules/EventDot'

// ─── API response types ───────────────────────────────────────────────────────

interface ApiGradeComponent {
  id: string
  name: string
  weight: number
  value: number | null
  published: boolean
}

interface ApiSubjectGrade {
  disciplina: string
  docente?: string
  semestre?: string
  turma?: string
  components: ApiGradeComponent[]
  nota_final: number | null
  resultado: 'aprovado' | 'reprovado' | null
  pendente: boolean
}

interface ApiGradesResponse {
  student_number?: string
  turma?: string
  disciplina?: string
  semestre?: string
  turno?: string
  subjects: ApiSubjectGrade[]
}

interface ApiCalendarEvent {
  id: string
  date: string
  type: string
  title: string
  time?: string
  location?: string
  description?: string
}

interface ApiCalendarResponse {
  events: ApiCalendarEvent[]
}

// ─── Data mappers ────────────────────────────────────────────────────────────

function mapSubject(s: ApiSubjectGrade): StudentSubjectGrade {
  return {
    disciplina: s.disciplina,
    docente: s.docente,
    semestre: s.semestre,
    turma: s.turma,
    components: s.components.map((c) => ({
      id: c.id,
      name: c.name,
      weight: c.weight,
      value: c.value,
      published: c.published,
    })),
    notaFinal: s.nota_final,
    resultado: s.resultado,
    pendente: s.pendente,
  }
}

function mapEvent(e: ApiCalendarEvent): CalendarEvent {
  return {
    id: e.id,
    date: e.date,
    type: e.type as CalendarEvent['type'],
    title: e.title,
    time: e.time,
    location: e.location,
    description: e.description,
  }
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function PortalPage() {
  const { user, role } = useAuth()

  // AC1: role guard — redirect non-students
  if (role !== null && role !== 'estudante') {
    if (role === 'professor') return <Navigate to="/painel" replace />
    if (role === 'delegado') return <Navigate to="/delegado" replace />
    return <Navigate to="/" replace />
  }

  return <PortalContent userName={user?.name ?? 'Estudante'} />
}

function PortalContent({ userName }: { userName: string }) {
  const [gradesData, setGradesData] = useState<ApiGradesResponse | null>(null)
  const [calendarEvents, setCalendarEvents] = useState<CalendarEvent[]>([])
  const [gradesLoading, setGradesLoading] = useState(true)
  const [calendarLoading, setCalendarLoading] = useState(true)
  // AC13: session expiry detection
  const [sessionExpired, setSessionExpired] = useState(false)

  const loadGrades = useCallback(async () => {
    setGradesLoading(true)
    try {
      const data = await apiFetch<ApiGradesResponse>('/api/v1/portal/me/grades')
      setGradesData(data)
    } catch (err) {
      // AC13: 401 → session expired
      if (err instanceof Error && err.message.includes('401')) {
        setSessionExpired(true)
        return
      }
      throw err
    } finally {
      setGradesLoading(false)
    }
  }, [])

  const loadCalendar = useCallback(async () => {
    setCalendarLoading(true)
    try {
      const data = await apiFetch<ApiCalendarResponse>('/api/v1/portal/me/calendar')
      setCalendarEvents(data.events.map(mapEvent))
    } catch (err) {
      if (err instanceof Error && err.message.includes('401')) {
        setSessionExpired(true)
        return
      }
      throw err
    } finally {
      setCalendarLoading(false)
    }
  }, [])

  // Trigger once on mount — pattern from GradesPage (avoids set-state-in-effect lint rule)
  useState(() => { loadGrades(); loadCalendar() })

  // AC13: redirect on session expiry
  if (sessionExpired) {
    return <Navigate to="/login?expired=true" replace />
  }

  // T12: PDF download via window.print()
  const handleDownloadPdf = () => {
    window.print()
  }

  const whatsappNumber = import.meta.env.VITE_WHATSAPP_CHATBOT_NUMBER as string | undefined
  const whatsappUrl = whatsappNumber
    ? `https://wa.me/${whatsappNumber.replace(/\D/g, '')}`
    : 'https://wa.me/'

  const subjects = gradesData?.subjects.map(mapSubject) ?? []
  const firstName = userName.split(' ')[0]

  const contextInfo = gradesData
    ? [gradesData.turma, gradesData.disciplina, gradesData.semestre, gradesData.turno]
        .filter(Boolean)
        .join(' · ')
    : ''

  return (
    <StudentPortalLayout studentNumber={gradesData?.student_number}>
      {/* AC3: Welcome banner */}
      <div className="bg-card rounded-lg border border-border px-5 py-3 mb-5 flex flex-wrap items-center gap-x-4 gap-y-1">
        <span className="text-base font-semibold text-slate-800">
          👋 Olá, {firstName}!
        </span>
        {contextInfo && (
          <span className="text-sm text-muted-foreground">{contextInfo}</span>
        )}
      </div>

      {/* Main 2-column layout: 65%/35% desktop, single col mobile */}
      {/* AC11: mobile-first flex-col ≤640px; grid desktop */}
      <div className="flex flex-col gap-5 sm:grid sm:grid-cols-[60%_40%] xl:grid-cols-[65%_35%]">

        {/* LEFT: Grades section */}
        <section aria-live="polite" aria-label="Minhas Notas">
          {/* Section header with PDF button */}
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-bold text-foreground">Minhas Notas</h2>
            <button
              type="button"
              onClick={handleDownloadPdf}
              aria-label="Descarregar PDF das notas"
              className="min-w-[44px] min-h-[44px] inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted/50 transition-colors"
            >
              <><Download className="size-4" /> PDF</>
            </button>
          </div>

          {gradesLoading ? (
            <div className="bg-card rounded-lg border border-border p-8 text-center text-muted-foreground animate-pulse">
              A carregar notas…
            </div>
          ) : subjects.length === 0 ? (
            <div className="bg-card rounded-lg border border-border p-8 text-center text-muted-foreground">
              Sem notas disponíveis para este semestre.
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {subjects.map((subject, idx) => (
                <StudentGradeCard
                  key={`${subject.disciplina}-${idx}`}
                  subject={subject}
                />
              ))}
            </div>
          )}
        </section>

        {/* RIGHT: Calendar + Events */}
        <aside className="flex flex-col gap-4">
          {/* AC8: Mini calendar */}
          {calendarLoading ? (
            <div className="bg-card rounded-lg border border-border p-4 text-center text-muted-foreground animate-pulse h-48">
              A carregar calendário…
            </div>
          ) : (
            <MonthCalendar events={calendarEvents} />
          )}

          {/* AC9: Upcoming events */}
          {!calendarLoading && (
            <UpcomingEventsList events={calendarEvents} />
          )}

          {/* AC10: WhatsApp chatbot banner */}
          <div className="bg-success/10 border border-success/20 rounded-lg px-4 py-4 flex flex-col gap-3">
            <div>
              <p className="font-semibold text-success text-sm">
                💬 Tem dúvidas sobre as suas notas?
              </p>
              <p className="text-xs text-success mt-1">
                Envie mensagem para o chatbot via WhatsApp e obtenha resposta
                imediata sobre os seus resultados publicados.
              </p>
            </div>
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Abrir chatbot no WhatsApp (abre nova janela)"
              className="min-w-[44px] min-h-[44px] inline-flex items-center justify-center gap-2 px-4 py-2 rounded-md bg-success hover:bg-success/90 text-white text-sm font-medium transition-colors self-start"
            >
              💬 Abrir WhatsApp
            </a>
          </div>
        </aside>
      </div>
    </StudentPortalLayout>
  )
}
