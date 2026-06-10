// StudentGradeCard — displays published grades for one subject
// T6: component table + badge; T7: unpublished state with friendly message (AC4–AC6)

import { Clock, CheckCircle, XCircle, User, Calendar, Building2, Download } from 'lucide-react'

export interface GradeComponentResult {
  id: string
  name: string
  weight: number
  value: number | null
  published: boolean
}

export interface StudentSubjectGrade {
  disciplina: string
  docente?: string
  semestre?: string
  turma?: string
  components: GradeComponentResult[]
  notaFinal: number | null
  resultado: 'aprovado' | 'reprovado' | null
  pendente: boolean
}

interface StudentGradeCardProps {
  subject: StudentSubjectGrade
  onDownloadPdf?: () => void
}

function formatGrade(value: number | null): string {
  if (value === null || value === undefined) return '—'
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

export function StudentGradeCard({ subject, onDownloadPdf }: StudentGradeCardProps) {
  if (subject.pendente) {
    return (
      <div className="bg-card rounded-lg border border-border p-5">
        <h3 className="font-semibold text-foreground mb-3">{subject.disciplina}</h3>
        <div className="flex items-start gap-3 bg-warning/10 border border-warning/20 rounded-lg px-4 py-3">
          <Clock className="size-5 text-warning mt-0.5 shrink-0" />
          <p className="text-sm text-warning">
            As notas desta disciplina ainda não foram publicadas pelo docente.
            Receberá uma notificação via WhatsApp quando disponíveis.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-card rounded-lg border border-border p-5">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="font-semibold text-foreground">{subject.disciplina}</h3>
          <div className="flex flex-wrap gap-x-3 text-xs text-muted-foreground mt-0.5">
            {subject.docente && <span className="flex items-center gap-1"><User className="size-3" /> {subject.docente}</span>}
            {subject.semestre && <span className="flex items-center gap-1"><Calendar className="size-3" /> {subject.semestre}</span>}
            {subject.turma && <span className="flex items-center gap-1"><Building2 className="size-3" /> {subject.turma}</span>}
          </div>
        </div>
        {onDownloadPdf && (
          <button
            type="button"
            onClick={onDownloadPdf}
            aria-label="Descarregar PDF das notas"
            className="min-w-[44px] min-h-[44px] flex items-center gap-1.5 px-3 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted transition-colors whitespace-nowrap"
          >
            <Download className="size-4" /> PDF
          </button>
        )}
      </div>

      <div className="overflow-x-auto -mx-1">
        <table
          className="w-full text-sm border-collapse"
          aria-label={`Notas de ${subject.disciplina}`}
        >
          <thead>
            <tr className="border-b border-border">
              <th scope="col" className="text-left py-2 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Componente
              </th>
              <th scope="col" className="text-center py-2 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wide whitespace-nowrap">
                Peso %
              </th>
              <th scope="col" className="text-center py-2 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Nota
              </th>
              <th scope="col" className="text-center py-2 px-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {subject.components.map((comp) => (
              <tr key={comp.id} className="hover:bg-muted/50">
                <th scope="row" className="text-left py-2 px-2 font-normal text-foreground">
                  {comp.name}
                </th>
                <td className="text-center py-2 px-2 text-muted-foreground">
                  {comp.weight}%
                </td>
                <td className="text-center py-2 px-2 font-medium text-foreground">
                  {formatGrade(comp.value)}
                </td>
                <td className="text-center py-2 px-2">
                  {comp.published
                    ? <span className="text-success text-xs flex items-center justify-center gap-1"><CheckCircle className="size-3" /> Lançada</span>
                    : <span className="text-muted-foreground text-xs">— Pendente</span>
                  }
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-border bg-muted/50">
              <th scope="row" className="text-left py-2 px-2 font-semibold text-foreground">
                Nota Final
              </th>
              <td />
              <td className="text-center py-2 px-2 font-bold text-foreground text-base">
                {formatGrade(subject.notaFinal)}
              </td>
              <td className="text-center py-2 px-2 text-xs text-success">
                <span className="flex items-center justify-center gap-1"><CheckCircle className="size-3" /> Publicada</span>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {subject.resultado !== null && (
        <div className="mt-4 pt-3 border-t border-border">
          <span
            className={[
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-bold',
              subject.resultado === 'aprovado'
                ? 'bg-success/10 text-success'
                : 'bg-destructive/10 text-destructive',
            ].join(' ')}
          >
            {subject.resultado === 'aprovado'
              ? <><CheckCircle className="size-4" /> APROVADO(A)</>
              : <><XCircle className="size-4" /> REPROVADO(A)</>
            }
          </span>
        </div>
      )}
    </div>
  )
}
