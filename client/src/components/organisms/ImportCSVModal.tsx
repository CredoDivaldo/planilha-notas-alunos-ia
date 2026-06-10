import { useState, useRef, useEffect } from 'react'
import { Download, X, CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
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
  const dataLines = lines.slice(1)
  const allRows: ParsedRow[] = dataLines.map((line) => {
    const parts = line.split(',').map((p) => p.trim())
    return {
      numero: parts[0] ?? '',
      nome: parts[1] ?? '',
      nota: parts[2] ?? '',
      valid: Boolean(
        parts[0] && parts[2] &&
        !isNaN(parseFloat(parts[2])) &&
        parseFloat(parts[2]) >= 0 &&
        parseFloat(parts[2]) <= 20
      ),
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

  const [selectedComponent, setSelectedComponent] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<ParsedRow[]>([])
  const [totalValid, setTotalValid] = useState(0)
  const [totalRows, setTotalRows] = useState(0)
  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isOpen) return
    const el = dialogRef.current
    if (!el) return

    const focusable = el.querySelectorAll<HTMLElement>(
      'button, input, select, [tabindex]:not([tabindex="-1"])',
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
        className="bg-card rounded-xl shadow-xl border border-border w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Download className="size-5 text-primary" />
            <h2 id="import-csv-title" className="text-lg font-semibold text-foreground">
              Importar Notas via CSV
            </h2>
          </div>
          <Button variant="ghost" size="icon-sm" onClick={handleClose} aria-label="Fechar">
            <X className="size-4" />
          </Button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 flex flex-col gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="import-component">
              Componente de Avaliação <span className="text-destructive">*</span>
            </Label>
            <Select value={selectedComponent} onValueChange={setSelectedComponent}>
              <SelectTrigger id="import-component">
                <SelectValue placeholder="Seleccionar componente…" />
              </SelectTrigger>
              <SelectContent>
                {components.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name} ({c.weight}%)
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <FileDropzone
            onFileSelect={handleFileSelect}
            accept=".csv"
            label={selectedFile ? `Ficheiro: ${selectedFile.name}` : 'Arraste o CSV aqui ou clique para seleccionar'}
          />

          {preview.length > 0 && (
            <div>
              <p className="text-sm font-medium text-foreground mb-2">
                Pré-visualização (primeiras {preview.length} linhas):
              </p>
              <table className="w-full text-xs border border-border rounded-md overflow-hidden">
                <thead>
                  <tr className="bg-muted border-b border-border">
                    <th scope="col" className="text-left px-3 py-1.5 font-medium text-muted-foreground">Nº</th>
                    <th scope="col" className="text-left px-3 py-1.5 font-medium text-muted-foreground">Nome</th>
                    <th scope="col" className="text-right px-3 py-1.5 font-medium text-muted-foreground">Nota</th>
                    <th scope="col" className="text-center px-3 py-1.5 font-medium text-muted-foreground">Válido</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, i) => (
                    <tr key={i} className={row.valid ? '' : 'bg-destructive/5'}>
                      <td className="px-3 py-1 border-b border-border">{row.numero || '—'}</td>
                      <td className="px-3 py-1 border-b border-border">{row.nome || '—'}</td>
                      <td className="px-3 py-1 border-b border-border text-right">{row.nota || '—'}</td>
                      <td className="px-3 py-1 border-b border-border text-center">
                        {row.valid
                          ? <CheckCircle className="size-3.5 text-success inline" />
                          : <XCircle className="size-3.5 text-destructive inline" />
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div role="status" aria-live="polite" className="mt-2 text-xs flex gap-3">
                <span className="text-success font-medium flex items-center gap-1">
                  <CheckCircle className="size-3" /> {totalValid} válidos
                </span>
                {totalRows - totalValid > 0 && (
                  <span className="text-warning flex items-center gap-1">
                    <AlertTriangle className="size-3" /> {totalRows - totalValid} sem correspondência
                  </span>
                )}
                <span className="text-muted-foreground">de {totalRows} total</span>
              </div>
            </div>
          )}

          {result && (
            <div role="status" aria-live="polite" className="rounded-lg bg-success/10 border border-success/20 px-3 py-2 text-sm text-success flex items-center gap-2">
              <CheckCircle className="size-4 shrink-0" />
              {result.imported} notas importadas
              {result.unmatched > 0 && ` | ${result.unmatched} sem correspondência`}
            </div>
          )}

          {error && (
            <div role="alert" className="rounded-lg bg-destructive/10 border border-destructive/20 px-3 py-2 text-sm text-destructive flex items-center gap-2">
              <XCircle className="size-4 shrink-0" />
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-border flex justify-end gap-2">
          <Button variant="outline" onClick={handleClose} disabled={importing}>
            Cancelar
          </Button>
          <Button
            onClick={handleImport}
            disabled={!selectedComponent || !selectedFile || importing}
          >
            {importing ? 'A importar…' : 'Importar'}
          </Button>
        </div>
      </div>
    </div>
  )
}
