import type { StepStatus } from '@/components/organisms/StepCard'

interface Step {
  label: string
  status: StepStatus
}

interface ProgressStepperProps {
  steps: Step[]
}

const STEP_ICONS: Record<StepStatus, string> = {
  completed: '✅',
  active: '▶',
  locked: '🔒',
  error: '❌',
}

export function ProgressStepper({ steps }: ProgressStepperProps) {
  return (
    <nav aria-label="Progresso das etapas" className="flex items-center w-full mb-6">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1
        const prevCompleted = index > 0 && steps[index - 1].status === 'completed'

        return (
          <div key={index} className="flex items-center flex-1">
            {/* Step indicator */}
            <div className="flex flex-col items-center gap-1 min-w-0">
              <div
                aria-current={step.status === 'active' ? 'step' : undefined}
                className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold transition-all ${
                  step.status === 'active'
                    ? 'bg-[#0D6EFD] text-white animate-pulse ring-2 ring-[#0D6EFD]/30'
                    : step.status === 'completed'
                    ? 'bg-[#15803D] text-white'
                    : step.status === 'error'
                    ? 'bg-[#B91C1C] text-white'
                    : 'bg-slate-200 text-slate-500'
                }`}
              >
                {step.status === 'active'
                  ? index + 1
                  : STEP_ICONS[step.status]}
              </div>
              <span
                className={`text-xs text-center leading-tight max-w-[70px] ${
                  step.status === 'active'
                    ? 'text-[#0D6EFD] font-bold'
                    : step.status === 'completed'
                    ? 'text-[#15803D] font-medium'
                    : step.status === 'error'
                    ? 'text-[#B91C1C]'
                    : 'text-slate-400'
                }`}
              >
                {step.label}
              </span>
            </div>

            {/* Connector */}
            {!isLast && (
              <div
                className={`flex-1 h-0.5 mx-2 mb-4 ${
                  prevCompleted || step.status === 'completed'
                    ? 'bg-[#15803D]'
                    : 'bg-slate-200'
                }`}
                aria-hidden="true"
              />
            )}
          </div>
        )
      })}
    </nav>
  )
}
