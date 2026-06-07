import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Button } from '@/components/ui/button'

export interface DelegateStudent {
  id: string
  studentNumber: string
  name: string
  subject: string
  grade: number | null
  published: boolean
  result: 'aprovado' | 'reprovado' | 'pendente'
  contactStatus: 'ok' | 'invalid' | 'missing'
  phone?: string
}

const RESULT_BADGE: Record<DelegateStudent['result'], { label: string; cls: string }> = {
  aprovado: {
    label: 'Aprovado',
    cls: 'bg-[#DCFCE7] text-[#15803D]',
  },
  reprovado: {
    label: 'Reprovado',
    cls: 'bg-[#FEE2E2] text-[#B91C1C]',
  },
  pendente: {
    label: '⏳ Pendente',
    cls: 'bg-[#FEF9C3] text-[#854D0E]',
  },
}

const CONTACT_BADGE: Record<DelegateStudent['contactStatus'], { label: string; cls: string }> = {
  ok: {
    label: '✅ OK',
    cls: 'bg-[#DCFCE7] text-[#15803D]',
  },
  invalid: {
    label: '⚠️ Inválido',
    cls: 'bg-[#FEF9C3] text-[#854D0E]',
  },
  missing: {
    label: '⚠️ Sem telefone',
    cls: 'bg-[#FEE2E2] text-[#B91C1C]',
  },
}

const PAGE_SIZE = 10

interface DelegateGradeTableProps {
  students: DelegateStudent[]
  turma?: string
  currentPage: number
  onPageChange: (page: number) => void
}

export function DelegateGradeTable({
  students,
  turma = 'ING-T1',
  currentPage,
  onPageChange,
}: DelegateGradeTableProps) {
  const totalPages = Math.max(1, Math.ceil(students.length / PAGE_SIZE))
  const safePage = Math.min(currentPage, totalPages)
  const pageStudents = students.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border border-slate-200">
        <Table aria-label={`Lista de estudantes da turma ${turma}`}>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead scope="col" className="w-28 font-semibold text-slate-700">
                Nº Estudante
              </TableHead>
              <TableHead scope="col" className="font-semibold text-slate-700">
                Nome
              </TableHead>
              <TableHead scope="col" className="font-semibold text-slate-700">
                Disciplina
              </TableHead>
              <TableHead scope="col" className="font-semibold text-slate-700 text-center w-20">
                Nota
              </TableHead>
              <TableHead scope="col" className="font-semibold text-slate-700 text-center w-32">
                Resultado
              </TableHead>
              <TableHead scope="col" className="font-semibold text-slate-700 text-center w-36">
                Contacto
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pageStudents.map((student) => {
              const resultInfo = RESULT_BADGE[student.result]
              const contactInfo = CONTACT_BADGE[student.contactStatus]
              const gradeDisplay =
                student.published && student.grade !== null
                  ? String(student.grade)
                  : '—'

              return (
                <TableRow key={student.id} className="hover:bg-slate-50/50">
                  <TableHead
                    scope="row"
                    className="font-mono text-sm font-normal text-slate-600 px-4 py-3"
                  >
                    {student.studentNumber}
                  </TableHead>
                  <TableCell className="font-medium text-slate-900">{student.name}</TableCell>
                  <TableCell className="text-slate-700">{student.subject}</TableCell>
                  <TableCell className="text-center tabular-nums text-slate-900">
                    {gradeDisplay}
                  </TableCell>
                  <TableCell className="text-center">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${resultInfo.cls}`}
                      aria-label={`Resultado: ${resultInfo.label}`}
                    >
                      {resultInfo.label}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${contactInfo.cls}`}
                      aria-label={`Contacto: ${contactInfo.label}`}
                    >
                      {contactInfo.label}
                    </span>
                  </TableCell>
                </TableRow>
              )
            })}

            {pageStudents.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="text-center text-slate-500 py-10"
                >
                  Nenhum estudante corresponde à pesquisa.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination — AC8 */}
      <div className="flex items-center justify-center gap-4 py-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(safePage - 1)}
          disabled={safePage <= 1}
          aria-label="Página anterior"
        >
          ← Anterior
        </Button>
        <span className="text-sm text-slate-600" aria-live="polite" aria-atomic="true">
          Página {safePage} de {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(safePage + 1)}
          disabled={safePage >= totalPages}
          aria-label="Próxima página"
        >
          Seguinte →
        </Button>
      </div>
    </div>
  )
}
