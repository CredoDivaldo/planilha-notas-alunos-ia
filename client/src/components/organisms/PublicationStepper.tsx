// PublicationStepper — O08 — 4-step publication wizard stepper
// Distinct from ProgressStepper (5-step upload flow with locked/error states)
// States: 'pending' | 'active' | 'completed'
// Completed steps are clickable (navigate back without data loss)

import { Check } from 'lucide-react'

export type PublicationStepState = 'pending' | 'active' | 'completed'

interface PublicationStep {
  label: string
  state: PublicationStepState
}

interface PublicationStepperProps {
  steps: PublicationStep[]
  onStepClick?: (index: number) => void
}

const STEP_LABELS = ['① Revisão', '② Audiência', '③ Canais', '④ Confirmar']

export function PublicationStepper({ steps, onStepClick }: PublicationStepperProps) {
  return (
    <nav aria-label="Passos da publicação" className="flex items-start w-full mb-6">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1
        const isClickable = step.state === 'completed' && onStepClick != null
        const stepNumber = STEP_LABELS[index] ?? `${index + 1}`

        return (
          <div key={index} className="flex items-center flex-1">
            <div className="flex flex-col items-center gap-1 min-w-0">
              {isClickable ? (
                <button
                  type="button"
                  onClick={() => onStepClick(index)}
                  aria-label={`Voltar ao passo ${index + 1}: ${step.label}`}
                  className="flex items-center justify-center w-9 h-9 rounded-full text-sm font-bold transition-all cursor-pointer bg-success text-white hover:bg-success/80 focus-visible:ring-2 focus-visible:ring-success/50 focus-visible:outline-none"
                >
                  <Check className="size-4" />
                </button>
              ) : (
                <div
                  aria-current={step.state === 'active' ? 'step' : undefined}
                  className={[
                    'flex items-center justify-center w-9 h-9 rounded-full text-sm font-bold transition-all',
                    step.state === 'active'
                      ? 'bg-primary text-primary-foreground ring-2 ring-primary/30'
                      : step.state === 'completed'
                      ? 'bg-success text-white'
                      : 'bg-muted text-muted-foreground',
                  ].join(' ')}
                >
                  {step.state === 'completed' ? <Check className="size-4" /> : index + 1}
                </div>
              )}

              <span
                className={[
                  'text-xs text-center leading-tight max-w-[72px] hidden sm:block',
                  step.state === 'active'
                    ? 'text-primary font-semibold'
                    : step.state === 'completed'
                    ? 'text-success font-medium'
                    : 'text-muted-foreground',
                ].join(' ')}
              >
                {stepNumber}
              </span>
            </div>

            {!isLast && (
              <div
                className={[
                  'flex-1 h-0.5 mx-2 mb-5',
                  step.state === 'completed' ? 'bg-success' : 'bg-border',
                ].join(' ')}
                aria-hidden="true"
              />
            )}
          </div>
        )
      })}
    </nav>
  )
}
