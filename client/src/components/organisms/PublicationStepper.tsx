// PublicationStepper — O08 — 4-step publication wizard stepper
// Distinct from ProgressStepper (5-step upload flow with locked/error states)
// States: 'pending' | 'active' | 'completed'
// Completed steps are clickable (navigate back without data loss)

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
            {/* Step indicator */}
            <div className="flex flex-col items-center gap-1 min-w-0">
              {isClickable ? (
                <button
                  type="button"
                  onClick={() => onStepClick(index)}
                  aria-label={`Voltar ao passo ${index + 1}: ${step.label}`}
                  className={[
                    'flex items-center justify-center w-9 h-9 rounded-full text-sm font-bold transition-all cursor-pointer',
                    'bg-[#15803D] text-white hover:bg-[#15803D]/80 focus-visible:ring-2 focus-visible:ring-[#15803D]/50 focus-visible:outline-none',
                  ].join(' ')}
                >
                  ✅
                </button>
              ) : (
                <div
                  aria-current={step.state === 'active' ? 'step' : undefined}
                  className={[
                    'flex items-center justify-center w-9 h-9 rounded-full text-sm font-bold transition-all',
                    step.state === 'active'
                      ? 'bg-[#0D6EFD] text-white ring-2 ring-[#0D6EFD]/30'
                      : step.state === 'completed'
                      ? 'bg-[#15803D] text-white'
                      : 'bg-slate-200 text-slate-400',
                  ].join(' ')}
                >
                  {step.state === 'completed' ? '✅' : index + 1}
                </div>
              )}

              <span
                className={[
                  'text-xs text-center leading-tight max-w-[72px] hidden sm:block',
                  step.state === 'active'
                    ? 'text-[#0D6EFD] font-semibold'
                    : step.state === 'completed'
                    ? 'text-[#15803D] font-medium'
                    : 'text-slate-400',
                ].join(' ')}
              >
                {stepNumber}
              </span>
            </div>

            {/* Connector line */}
            {!isLast && (
              <div
                className={[
                  'flex-1 h-0.5 mx-2 mb-5',
                  step.state === 'completed' ? 'bg-[#15803D]' : 'bg-slate-200',
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
