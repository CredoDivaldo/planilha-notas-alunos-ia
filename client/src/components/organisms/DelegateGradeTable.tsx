import { Clock, CheckCircle, AlertTriangle, XCircle, ChevronLeft, ChevronRight } from 'lucide-react'
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

const RESULT_BADGE: Record<DelegateStudent['result'], { label: string; cls: string; icon: React.ReactNode }> = {
  aprovado: {
    label: 'Aprovado',
    cls: 'bg-success/10 text-success',
    icon: <CheckCircle className="size-3" />,
  },
  reprovado: {
    label: 'Reprovado',
    cls: 'bg-destructive/10 text-destructive',
    icon: <XCircle className="size-3" />,
  },
  pendente: {
    label: 'Pendente',
    cls: 'bg-warning/10 text-warning',
    icon: <Clock className="size-3" />,
  },
}

const CONTACT_BADGE: Record<DelegateStudent['contactStatus'], { label: string; cls: string; icon: React.ReactNode }> = {
  ok: {
    label: 'OK',
    cls: 'bg-success/10 text-success',
    icon: <CheckCircle className="size-3" />,
  },
  invalid: {
    label: 'Inválido',
    cls: 'bg-warning/10 text-warning',
    icon: <AlertTriangle className="size-3" />,
  },
  missing: {
    label: 'Sem telefone',
    cls: 'bg-destructive/10 text-destructive',
    icon: <AlertTriangle className="size-3" />,
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
      <div className="overflow-x-auto rounded-lg border border-border">
        <Table aria-label={`Lista de estudantes da turma ${turma}`}>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead scope="col" className="w-28 font-semibold text-foreground">
                Nº Estudante
              </TableHead>
              <TableHead scope="col" className="font-semibold text-foreground">
                Nome
              </TableHead>
              <TableHead scope="col" className="font-semibold text-foreground">
                Disciplina
              </TableHead>
              <TableHead scope="col" className="font-semibold text-foreground text-center w-20">
                Nota
              </TableHead>
              <TableHead scope="col" className="font-semibold text-foreground text-center w-32">
                Resultado
              </TableHead>
              <TableHead scope="col" className="font-semibold text-foreground text-center w-36">
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
                <TableRow key={student.id} className="hover:bg-muted/30">
                  <TableHead
                    scope="row"
                    className="font-mono text-sm font-normal text-muted-foreground px-4 py-3"
                  >
                    {student.studentNumber}
                  </TableHead>
                  <TableCell className="font-medium text-foreground">{student.name}</TableCell>
                  <TableCell className="text-foreground">{student.subject}</TableCell>
                  <TableCell className="text-center tabular-nums text-foreground">
                    {gradeDisplay}
                  </TableCell>
                  <TableCell className="text-center">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${resultInfo.cls}`}
                      aria-label={`Resultado: ${resultInfo.label}`}
                    >
                      {resultInfo.icon} {resultInfo.label}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${contactInfo.cls}`}
                      aria-label={`Contacto: ${contactInfo.label}`}
                    >
                      {contactInfo.icon} {contactInfo.label}
                    </span>
                  </TableCell>
                </TableRow>
              )
            })}

            {pageStudents.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={6}
                  className="text-center text-muted-foreground py-10"
                >
                  Nenhum estudante corresponde à pesquisa.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-center gap-4 py-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(safePage - 1)}
          disabled={safePage <= 1}
          aria-label="Página anterior"
          className="gap-1"
        >
          <ChevronLeft className="size-4" /> Anterior
        </Button>
        <span className="text-sm text-muted-foreground" aria-live="polite" aria-atomic="true">
          Página {safePage} de {totalPages}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onPageChange(safePage + 1)}
          disabled={safePage >= totalPages}
          aria-label="Próxima página"
          className="gap-1"
        >
          Seguinte <ChevronRight className="size-4" />
        </Button>
      </div>
    </div>
  )
}
