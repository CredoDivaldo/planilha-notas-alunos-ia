import type { GradeValue, ContextItem } from '@/types'

// Calcula a nota final no frontend (mostra logo o valor ao professor sem esperar
// pelo servidor). É a MESMA média ponderada do backend (professor.py): se faltar
// alguma componente devolve null; senão soma (nota × peso/100) e arredonda a 1 casa.
export function calcNotaFinal(
  components: Record<string, GradeValue>,
  contextComponents: ContextItem['components'],
): number | null {
  // Se alguma componente não tiver nota, a final ainda não pode ser calculada.
  for (const comp of contextComponents) {
    const val = components[comp.id]?.value
    if (val === null || val === undefined) return null
  }
  // reduce: percorre as componentes acumulando a soma ponderada (parte × peso).
  const total = contextComponents.reduce((sum, comp) => {
    const val = components[comp.id]?.value ?? 0
    return sum + (val * comp.weight) / 100
  }, 0)
  return Math.round(total * 10) / 10  // arredonda a 1 casa decimal
}

// Decide a "etiqueta" de estado a mostrar na linha do aluno consoante quantas
// componentes estão preenchidas e se já foi publicada.
export function getRowBadgeLabel(
  components: Record<string, GradeValue>,
  contextComponents: ContextItem['components'],
  published: boolean,
): 'Publicada' | 'Lançada' | 'Incompleta' | 'Vazio' {
  if (published) return 'Publicada'
  // Conta quantas componentes têm valor (filter mantém só as preenchidas).
  const vals = contextComponents.map((c) => components[c.id]?.value)
  const filled = vals.filter((v) => v !== null && v !== undefined).length
  if (filled === 0) return 'Vazio'
  if (filled < contextComponents.length) return 'Incompleta'
  return 'Lançada'
}

export const BADGE_CLASSES: Record<string, string> = {
  Publicada: 'bg-blue-100 text-blue-700',
  Lançada: 'bg-green-100 text-green-700',
  Incompleta: 'bg-amber-100 text-amber-700',
  Vazio: 'bg-red-100 text-red-700',
}
