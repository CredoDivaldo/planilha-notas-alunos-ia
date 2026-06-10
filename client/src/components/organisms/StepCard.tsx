import type { ReactNode } from 'react'
import { CheckCircle, Play, Lock, AlertCircle, X } from 'lucide-react'

export type StepStatus = 'locked' | 'active' | 'completed' | 'error'

interface StepCardProps {
  stepNumber: number
  title: string
  status: StepStatus
  preconditions?: string[]
  children?: ReactNode
}

const STATUS_STYLES: Record<StepStatus, string> = {
  completed: 'bg-card border border-border border-l-4 border-l-success rounded-lg',
  active: 'bg-card border border-border border-l-4 border-l-primary rounded-lg shadow-sm',
  locked: 'bg-muted/30 border border-border rounded-lg',
  error: 'bg-card border border-border border-l-4 border-l-destructive rounded-lg',
}

const HEADER_STYLES: Record<StepStatus, string> = {
  completed: 'text-success',
  active: 'text-primary',
  locked: 'text-muted-foreground',
  error: 'text-destructive',
}

const BADGE_STYLES: Record<StepStatus, string> = {
  active: 'bg-primary text-primary-foreground animate-pulse',
  completed: 'bg-success text-white',
  error: 'bg-destructive text-white',
  locked: 'bg-muted text-muted-foreground',
}

function StatusIcon({ status, stepNumber }: { status: StepStatus; stepNumber: number }) {
  if (status === 'completed') return <CheckCircle className="size-4" />
  if (status === 'error') return <AlertCircle className="size-4" />
  if (status === 'locked') return <Lock className="size-3.5" />
  if (status === 'active') return <Play className="size-3.5 fill-current" />
  return <span className="text-xs font-bold">{stepNumber}</span>
}

export function StepCard({ stepNumber, title, status, preconditions, children }: StepCardProps) {
  const isExpanded = status === 'active' || status === 'completed' || status === 'error'
  const isLocked = status === 'locked'

  return (
    <div
      className={STATUS_STYLES[status]}
      aria-current={status === 'active' ? 'step' : undefined}
    >
      {/* Header */}
      <div className={`flex items-center gap-3 px-4 py-3 ${isLocked ? 'opacity-60' : ''}`}>
        <div
          className={`flex items-center justify-center w-7 h-7 rounded-full ${BADGE_STYLES[status]}`}
        >
          <StatusIcon status={status} stepNumber={stepNumber} />
        </div>
        <span className={`font-semibold text-sm ${HEADER_STYLES[status]}`}>
          Passo {stepNumber}: {title}
        </span>
        {isLocked && (
          <span className="ml-auto text-xs text-muted-foreground">Bloqueado</span>
        )}
        {status === 'completed' && (
          <span className="ml-auto text-xs text-success font-medium">Concluído</span>
        )}
      </div>

      {/* Body */}
      {isExpanded && (
        <div className="px-4 pb-4">
          <div className="border-t border-border pt-3">
            {children}
          </div>
        </div>
      )}

      {/* Locked preconditions */}
      {isLocked && preconditions && preconditions.length > 0 && (
        <div className="px-4 pb-3">
          <p className="text-xs text-muted-foreground font-medium mb-1">Pré-condições em falta:</p>
          <ul className="space-y-1">
            {preconditions.map((pre, i) => (
              <li key={i} className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <X className="size-3 text-destructive shrink-0" />
                {pre}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
