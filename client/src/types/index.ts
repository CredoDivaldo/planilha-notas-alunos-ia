export interface User {
  id: string
  name: string
  role: 'professor' | 'estudante' | 'delegado'
  token: string
}

export interface AcademicContext {
  id: string
  name: string
  year: string
  semester: string
}

export interface Grade {
  studentId: string
  studentName: string
  value: number | null
  published: boolean
}

export interface GradeComponent {
  id: string
  name: string
  weight: number
}

export interface Delegado {
  id: string
  name: string
  studentNumber: string
}

export interface ContextItem {
  id: string
  turma: string
  disciplina: string
  semestre: string
  turno: string
  alunosCount: number
  delegado: Delegado | null
  components: GradeComponent[]
}

export interface GradeValue {
  gradeId: string
  value: number | null
}

export interface StudentRow {
  studentId: string
  studentNumber: string
  studentName: string
  phone: string | null
  components: Record<string, GradeValue>
  published: boolean
}

export interface ImportHistoryEntry {
  id: string
  componentName: string
  timestamp: string
  count: number
}
