import type { GradeValue, ContextItem } from '@/types'

export function calcNotaFinal(
  components: Record<string, GradeValue>,
  contextComponents: ContextItem['components'],
): number | null {
  for (const comp of contextComponents) {
    const val = components[comp.id]?.value
    if (val === null || val === undefined) return null
  }
  const total = contextComponents.reduce((sum, comp) => {
    const val = components[comp.id]?.value ?? 0
    return sum + (val * comp.weight) / 100
  }, 0)
  return Math.round(total * 10) / 10
}

export function getRowBadgeLabel(
  components: Record<string, GradeValue>,
  contextComponents: ContextItem['components'],
  published: boolean,
): 'Publicada' | 'Lançada' | 'Incompleta' | 'Vazio' {
  if (published) return 'Publicada'
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
