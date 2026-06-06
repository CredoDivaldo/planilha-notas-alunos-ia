import type { ReactNode } from 'react'

export type StepStatus = 'locked' | 'active' | 'completed' | 'error'

interface StepCardProps {
  stepNumber: number
  title: string
  status: StepStatus
  preconditions?: string[]
  children?: ReactNode
}

const STATUS_ICONS: Record<StepStatus, string> = {
  completed: '✅',
  active: '▶',
  locked: '🔒',
  error: '❌',
}

const STATUS_STYLES: Record<StepStatus, string> = {
  completed: 'bg-white border border-slate-200 border-l-4 border-l-[#15803D] rounded-lg',
  active: 'bg-white border border-slate-200 border-l-4 border-l-[#0D6EFD] rounded-lg shadow-sm',
  locked: 'bg-slate-50 border border-slate-200 rounded-lg',
  error: 'bg-white border border-slate-200 border-l-4 border-l-[#B91C1C] rounded-lg',
}

const HEADER_STYLES: Record<StepStatus, string> = {
  completed: 'text-[#15803D]',
  active: 'text-[#0D6EFD]',
  locked: 'text-slate-400',
  error: 'text-[#B91C1C]',
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
          className={`flex items-center justify-center w-7 h-7 rounded-full text-sm font-bold ${
            status === 'active'
              ? 'bg-[#0D6EFD] text-white animate-pulse'
              : status === 'completed'
              ? 'bg-[#15803D] text-white'
              : status === 'error'
              ? 'bg-[#B91C1C] text-white'
              : 'bg-slate-200 text-slate-500'
          }`}
        >
          {STATUS_ICONS[status] === '▶' ? stepNumber : STATUS_ICONS[status]}
        </div>
        <span className={`font-semibold text-sm ${HEADER_STYLES[status]}`}>
          Passo {stepNumber}: {title}
        </span>
        {isLocked && (
          <span className="ml-auto text-xs text-slate-400">Bloqueado</span>
        )}
        {status === 'completed' && (
          <span className="ml-auto text-xs text-[#15803D] font-medium">Concluído</span>
        )}
      </div>

      {/* Body */}
      {isExpanded && (
        <div className="px-4 pb-4">
          <div className="border-t border-slate-100 pt-3">
            {children}
          </div>
        </div>
      )}

      {/* Locked preconditions */}
      {isLocked && preconditions && preconditions.length > 0 && (
        <div className="px-4 pb-3">
          <p className="text-xs text-slate-400 font-medium mb-1">Pré-condições em falta:</p>
          <ul className="space-y-1">
            {preconditions.map((pre, i) => (
              <li key={i} className="flex items-center gap-1.5 text-xs text-slate-400">
                <span>❌</span>
                {pre}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
