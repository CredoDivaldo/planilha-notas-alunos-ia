import { Check, Play, Lock, X } from 'lucide-react'
import type { StepStatus } from '@/components/organisms/StepCard'

interface Step {
  label: string
  status: StepStatus
}

interface ProgressStepperProps {
  steps: Step[]
}

function StepIcon({ status, index }: { status: StepStatus; index: number }) {
  if (status === 'active') return <>{index + 1}</>
  if (status === 'completed') return <Check className="size-4" />
  if (status === 'error') return <X className="size-4" />
  if (status === 'locked') return <Lock className="size-3.5" />
  return <Play className="size-3.5" />
}

export function ProgressStepper({ steps }: ProgressStepperProps) {
  return (
    <nav aria-label="Progresso das etapas" className="flex items-center w-full mb-6">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1
        const prevCompleted = index > 0 && steps[index - 1].status === 'completed'

        return (
          <div key={index} className="flex items-center flex-1">
            <div className="flex flex-col items-center gap-1 min-w-0">
              <div
                aria-current={step.status === 'active' ? 'step' : undefined}
                className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold transition-all ${
                  step.status === 'active'
                    ? 'bg-primary text-primary-foreground animate-pulse ring-2 ring-primary/30'
                    : step.status === 'completed'
                    ? 'bg-success text-white'
                    : step.status === 'error'
                    ? 'bg-destructive text-destructive-foreground'
                    : 'bg-muted text-muted-foreground'
                }`}
              >
                <StepIcon status={step.status} index={index} />
              </div>
              <span
                className={`text-xs text-center leading-tight max-w-[70px] ${
                  step.status === 'active'
                    ? 'text-primary font-bold'
                    : step.status === 'completed'
                    ? 'text-success font-medium'
                    : step.status === 'error'
                    ? 'text-destructive'
                    : 'text-muted-foreground'
                }`}
              >
                {step.label}
              </span>
            </div>

            {!isLast && (
              <div
                className={`flex-1 h-0.5 mx-2 mb-4 ${
                  prevCompleted || step.status === 'completed'
                    ? 'bg-success'
                    : 'bg-border'
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
