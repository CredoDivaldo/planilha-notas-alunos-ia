import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { FileDropzone } from '@/components/molecules/FileDropzone'
import type { GradeComponent } from '@/types'

interface ParsedRow {
  numero: string
  nome: string
  nota: string
  valid: boolean
}

interface ImportResult {
  imported: number
  unmatched: number
}

interface ImportCSVModalProps {
  isOpen: boolean
  onClose: () => void
  components: GradeComponent[]
  onImport: (componentId: string, file: File) => Promise<ImportResult>
}

function parseCSVPreview(text: string): { preview: ParsedRow[]; totalValid: number; totalRows: number } {
  const lines = text.split('\n').filter((l) => l.trim())
  const dataLines = lines.slice(1) // skip header
  const allRows: ParsedRow[] = dataLines.map((line) => {
    const parts = line.split(',').map((p) => p.trim())
    return {
      numero: parts[0] ?? '',
      nome: parts[1] ?? '',
      nota: parts[2] ?? '',
      valid: Boolean(parts[0] && parts[2] && !isNaN(parseFloat(parts[2])) && parseFloat(parts[2]) >= 0 && parseFloat(parts[2]) <= 20),
    }
  })
  return {
    preview: allRows.slice(0, 3),
    totalValid: allRows.filter((r) => r.valid).length,
    totalRows: allRows.length,
  }
}

export function ImportCSVModal({ isOpen, onClose, components, onImport }: ImportCSVModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null)

  // Lazy initializers — modal remounts on each open (returns null when !isOpen)
  const [selectedComponent, setSelectedComponent] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<ParsedRow[]>([])
  const [totalValid, setTotalValid] = useState(0)
  const [totalRows, setTotalRows] = useState(0)
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Focus trap + Escape
  useEffect(() => {
    if (!isOpen) return
    const el = dialogRef.current
    if (!el) return

    const focusable = el.querySelectorAll<HTMLElement>(
      'button, input, select, textarea, [tabindex]:not([tabindex="-1"])',
    )
    focusable[0]?.focus()

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') { onClose(); return }
      if (e.key === 'Tab') {
        const first = focusable[0]
        const last = focusable[focusable.length - 1]
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault(); last?.focus()
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault(); first?.focus()
        }
      }
    }

    el.addEventListener('keydown', handleKeyDown)
    return () => el.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const handleFileSelect = (file: File) => {
    setSelectedFile(file)
    setResult(null)
    setError(null)
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      const parsed = parseCSVPreview(text)
      setPreview(parsed.preview)
      setTotalValid(parsed.totalValid)
      setTotalRows(parsed.totalRows)
    }
    reader.readAsText(file)
  }

  const handleImport = async () => {
    if (!selectedComponent || !selectedFile) return
    setImporting(true)
    setError(null)
    try {
      const res = await onImport(selectedComponent, selectedFile)
      setResult(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao importar')
    } finally {
      setImporting(false)
    }
  }

  const handleClose = () => {
    setSelectedComponent('')
    setSelectedFile(null)
    setPreview([])
    setTotalValid(0)
    setTotalRows(0)
    setResult(null)
    setError(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === e.currentTarget) handleClose() }}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-csv-title"
        className="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 id="import-csv-title" className="text-lg font-semibold text-slate-900">
            📥 Importar Notas via CSV
          </h2>
          <button
            type="button"
            onClick={handleClose}
            aria-label="Fechar modal"
            className="text-slate-400 hover:text-slate-700 transition-colors p-1 rounded"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 flex flex-col gap-4">
          {/* Component selector */}
          <div className="flex flex-col gap-1.5">
            <label htmlFor="import-component" className="text-sm font-medium text-slate-700">
              Componente de Avaliação <span className="text-[#B91C1C]">*</span>
            </label>
            <select
              id="import-component"
              value={selectedComponent}
              onChange={(e) => setSelectedComponent(e.target.value)}
              className="border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-[#0D6EFD] bg-white"
            >
              <option value="">Seleccionar componente…</option>
              {components.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.weight}%)
                </option>
              ))}
            </select>
          </div>

          {/* Dropzone */}
          <FileDropzone
            onFileSelect={handleFileSelect}
            accept=".csv"
            label={selectedFile ? `Ficheiro: ${selectedFile.name}` : 'Arraste o CSV aqui ou clique para seleccionar'}
          />

          {/* Preview */}
          {preview.length > 0 && (
            <div>
              <p className="text-sm font-medium text-slate-700 mb-2">
                Pré-visualização (primeiras {preview.length} linhas):
              </p>
              <table className="w-full text-xs border border-slate-200 rounded-md overflow-hidden">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    <th scope="col" className="text-left px-3 py-1.5 font-medium text-slate-600">Nº</th>
                    <th scope="col" className="text-left px-3 py-1.5 font-medium text-slate-600">Nome</th>
                    <th scope="col" className="text-right px-3 py-1.5 font-medium text-slate-600">Nota</th>
                    <th scope="col" className="text-center px-3 py-1.5 font-medium text-slate-600">Válido</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, i) => (
                    <tr key={i} className={row.valid ? '' : 'bg-red-50'}>
                      <td className="px-3 py-1 border-b border-slate-100">{row.numero || '—'}</td>
                      <td className="px-3 py-1 border-b border-slate-100">{row.nome || '—'}</td>
                      <td className="px-3 py-1 border-b border-slate-100 text-right">{row.nota || '—'}</td>
                      <td className="px-3 py-1 border-b border-slate-100 text-center">
                        {row.valid ? '✅' : '❌'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div
                role="status"
                aria-live="polite"
                className="mt-2 text-xs text-slate-600 flex gap-3"
              >
                <span className="text-[#15803D] font-medium">✅ {totalValid} registos válidos</span>
                {totalRows - totalValid > 0 && (
                  <span className="text-[#B45309]">⚠️ {totalRows - totalValid} sem correspondência</span>
                )}
                <span className="text-slate-400">de {totalRows} total</span>
              </div>
            </div>
          )}

          {/* Import result */}
          {result && (
            <div
              role="status"
              aria-live="polite"
              className="rounded bg-green-50 border border-green-200 px-3 py-2 text-sm text-[#15803D]"
            >
              ✅ {result.imported} notas importadas
              {result.unmatched > 0 && ` | ${result.unmatched} sem correspondência`}
            </div>
          )}

          {/* Error */}
          {error && (
            <div
              role="alert"
              className="rounded bg-red-50 border border-red-200 px-3 py-2 text-sm text-[#B91C1C]"
            >
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-200 flex justify-end gap-2">
          <Button variant="outline" onClick={handleClose} disabled={importing}>
            Cancelar
          </Button>
          <Button
            onClick={handleImport}
            disabled={!selectedComponent || !selectedFile || importing}
            className="bg-[#0D6EFD] hover:bg-[#0D6EFD]/90 text-white"
          >
            {importing
              ? 'A importar…'
              : totalValid > 0
              ? `Importar ${totalValid} notas`
              : 'Importar'}
          </Button>
        </div>
      </div>
    </div>
  )
}
