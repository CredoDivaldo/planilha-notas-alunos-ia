import { useRef, useState } from 'react'
import { cn } from '@/lib/utils'

interface FileDropzoneProps {
  onFileSelect: (file: File) => void
  accept?: string
  label?: string
  isLoading?: boolean
  error?: string
}

export function FileDropzone({
  onFileSelect,
  accept = '.csv',
  label = 'Arraste um ficheiro CSV ou clique para seleccionar',
  isLoading = false,
  error,
}: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragOver, setIsDragOver] = useState(false)

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) onFileSelect(file)
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = () => {
    setIsDragOver(false)
  }

  const handleClick = () => {
    if (!isLoading) inputRef.current?.click()
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onFileSelect(file)
      // Reset input value so the same file can be re-selected
      e.target.value = ''
    }
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label={label}
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleClick() }}
        className={cn(
          'border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors select-none',
          isDragOver
            ? 'border-[#0D6EFD] bg-[#0D6EFD]/5'
            : 'border-slate-300 hover:border-[#0D6EFD] hover:bg-slate-50',
          isLoading && 'opacity-60 cursor-wait',
        )}
      >
        <div className="flex flex-col items-center gap-2">
          <span className="text-2xl">📂</span>
          <p className="text-sm text-[#475569]">{label}</p>
          <p className="text-xs text-slate-400">Formatos aceites: {accept}</p>
          {isLoading && (
            <p className="text-xs text-[#0D6EFD] font-medium animate-pulse">A carregar…</p>
          )}
        </div>
      </div>
      {error && (
        <p role="alert" className="mt-1.5 text-sm text-[#B91C1C]">
          {error}
        </p>
      )}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
      />
    </div>
  )
}
