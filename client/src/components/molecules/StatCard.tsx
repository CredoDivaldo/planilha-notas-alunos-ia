import type { ReactNode } from 'react'

interface StatCardProps {
  icon: ReactNode
  label: string
  value: string | number
  variant?: 'default' | 'success' | 'warning' | 'danger'
}

const VARIANT_STYLES: Record<NonNullable<StatCardProps['variant']>, string> = {
  default: 'text-primary',
  success: 'text-success',
  warning: 'text-warning',
  danger: 'text-destructive',
}

export function StatCard({ icon, label, value, variant = 'default' }: StatCardProps) {
  return (
    <div
      className="flex flex-col items-center gap-1 p-3 bg-card rounded-lg border border-border"
      aria-live="polite"
      aria-atomic="true"
    >
      <span className={`${VARIANT_STYLES[variant]}`} aria-hidden="true">{icon}</span>
      <span className="text-xs text-muted-foreground text-center leading-tight">{label}</span>
      <span className="text-2xl font-bold text-foreground">{value}</span>
    </div>
  )
}
