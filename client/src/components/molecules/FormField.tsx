import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import type { InputHTMLAttributes } from 'react'

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string
  label: string
  error?: string
  helperText?: string
}

export function FormField({ id, label, error, helperText, className, ...props }: FormFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
        aria-invalid={!!error}
        className={cn(
          'focus-visible:outline-2 focus-visible:outline-[#0D6EFD]',
          error && 'border-[#B91C1C]',
          className
        )}
        {...props}
      />
      {error && (
        <p id={`${id}-error`} role="alert" aria-live="assertive" className="text-sm text-[#B91C1C]">
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={`${id}-helper`} className="text-sm text-[#475569]">{helperText}</p>
      )}
    </div>
  )
}
