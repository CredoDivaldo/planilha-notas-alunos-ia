// StudentGradeCard — displays published grades for one subject
// T6: component table + badge; T7: unpublished state with friendly message (AC4–AC6)

export interface GradeComponentResult {
  id: string
  name: string
  weight: number          // percentage 0-100
  value: number | null    // null → "—" (NEVER render as 0 or empty)
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
  /** false = grades published; true = pending publication */
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
  // AC5 / AC7: unpublished state
  if (subject.pendente) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-5">
        <h3 className="font-semibold text-slate-800 mb-3">{subject.disciplina}</h3>
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3">
          <span className="text-xl mt-0.5">⏳</span>
          <p className="text-sm text-amber-800">
            As notas desta disciplina ainda não foram publicadas pelo docente.
            Receberá uma notificação via WhatsApp quando disponíveis.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5">
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <h3 className="font-semibold text-slate-800">{subject.disciplina}</h3>
          <div className="flex flex-wrap gap-x-3 text-xs text-slate-500 mt-0.5">
            {subject.docente && <span>👤 {subject.docente}</span>}
            {subject.semestre && <span>📅 {subject.semestre}</span>}
            {subject.turma && <span>🏫 {subject.turma}</span>}
          </div>
        </div>
        {onDownloadPdf && (
          <button
            type="button"
            onClick={onDownloadPdf}
            aria-label="Descarregar PDF das notas"
            className="min-w-[44px] min-h-[44px] flex items-center gap-1.5 px-3 py-2 rounded-md border border-slate-300 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors whitespace-nowrap"
          >
            📥 PDF
          </button>
        )}
      </div>

      {/* Grade table — AC4 / AC6 */}
      <div className="overflow-x-auto -mx-1">
        <table
          className="w-full text-sm border-collapse"
          aria-label={`Notas de ${subject.disciplina}`}
        >
          <thead>
            <tr className="border-b border-slate-200">
              <th scope="col" className="text-left py-2 px-2 text-xs font-medium text-slate-500 uppercase tracking-wide">
                Componente
              </th>
              <th scope="col" className="text-center py-2 px-2 text-xs font-medium text-slate-500 uppercase tracking-wide whitespace-nowrap">
                Peso %
              </th>
              <th scope="col" className="text-center py-2 px-2 text-xs font-medium text-slate-500 uppercase tracking-wide">
                Nota
              </th>
              <th scope="col" className="text-center py-2 px-2 text-xs font-medium text-slate-500 uppercase tracking-wide">
                Estado
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {subject.components.map((comp) => (
              <tr key={comp.id} className="hover:bg-slate-50">
                <th scope="row" className="text-left py-2 px-2 font-normal text-slate-700">
                  {comp.name}
                </th>
                <td className="text-center py-2 px-2 text-slate-600">
                  {comp.weight}%
                </td>
                {/* AC6: null → "—", never "0" or empty */}
                <td className="text-center py-2 px-2 font-medium text-slate-800">
                  {formatGrade(comp.value)}
                </td>
                <td className="text-center py-2 px-2">
                  {comp.published
                    ? <span className="text-green-700 text-xs">✅ Lançada</span>
                    : <span className="text-slate-400 text-xs">— Pendente</span>
                  }
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t-2 border-slate-300 bg-slate-50">
              <th scope="row" className="text-left py-2 px-2 font-semibold text-slate-800">
                Nota Final
              </th>
              <td />
              <td className="text-center py-2 px-2 font-bold text-slate-900 text-base">
                {formatGrade(subject.notaFinal)}
              </td>
              <td className="text-center py-2 px-2 text-xs text-green-700">
                ✅ Publicada
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Result badge — AC4 */}
      {subject.resultado !== null && (
        <div className="mt-4 pt-3 border-t border-slate-100">
          <span
            className={[
              'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-bold',
              subject.resultado === 'aprovado'
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800',
            ].join(' ')}
          >
            {subject.resultado === 'aprovado' ? '✅ APROVADO(A)' : '❌ REPROVADO(A)'}
          </span>
        </div>
      )}
    </div>
  )
}
