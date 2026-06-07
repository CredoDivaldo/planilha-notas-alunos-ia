import type { DelegateStudent } from '@/components/organisms/DelegateGradeTable'

export function downloadCSV(students: DelegateStudent[]) {
  const headers = ['Nº', 'Nome', 'Disciplina', 'Nota', 'Resultado', 'Contacto']
  const rows = students.map((s) => [
    s.studentNumber,
    s.name,
    s.subject,
    s.published && s.grade !== null ? String(s.grade) : '—',
    s.result === 'aprovado' ? 'Aprovado' : s.result === 'reprovado' ? 'Reprovado' : 'Pendente',
    s.contactStatus === 'ok' ? 'OK' : s.contactStatus === 'invalid' ? 'Inválido' : 'Sem telefone',
  ])
  const csv = [headers, ...rows].map((r) => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'lista-turma.csv'
  a.click()
  URL.revokeObjectURL(url)
}
