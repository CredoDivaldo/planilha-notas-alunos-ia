import { useState, useRef, useEffect, useCallback } from 'react'
import { Download, X, CheckCircle, XCircle, AlertTriangle, Layers } from 'lucide-react'
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

interface MultiParsedRow {
  numero: string
  nome: string
  values: Record<string, string>
  validCount: number
  totalMatched: number
}

interface ImportResult {
  imported: number
  unmatched: number
}

interface MultiImportResult {
  total: number
  components: { csv_column: string; component_name: string; component_index: number; count: number }[]
  unmatched_columns: string[]
}

interface ColumnMatchInfo {
  csvColumn: string
  componentName: string
  componentIndex: number
}

interface ImportCSVModalProps {
  isOpen: boolean
  onClose: () => void
  components: GradeComponent[]
  onImport: (componentId: string, file: File) => Promise<ImportResult>
  onImportMulti?: (file: File) => Promise<MultiImportResult>
}

const NON_GRADE_HEADERS = new Set([
  'numero_estudante', 'numero', 'numeroaluno', 'id',
  'nome', 'aluno',
  'disciplina', 'subject', 'materia',
  'turma', 'telefone', 'phone', 'whatsapp',
  'resultado', 'result', 'media_final', 'media',
])

function normalize(s: string): string {
  return s.normalize('NFD').replace(/[̀-ͯ]/g, '').trim().toLowerCase().replace(/[_ ]/g, '')
}

function detectMultiColumns(headers: string[], components: GradeComponent[]): ColumnMatchInfo[] {
  const matches: ColumnMatchInfo[] = []
  for (const header of headers) {
    const nh = normalize(header)
    if (NON_GRADE_HEADERS.has(nh)) continue
    for (let i = 0; i < components.length; i++) {
      if (nh === normalize(components[i].name)) {
        matches.push({ csvColumn: header, componentName: components[i].name, componentIndex: i })
        break
      }
    }
  }
  return matches
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

function parseCSVHeaders(text: string): string[] {
  const firstLine = text.split('\n').find((l) => l.trim())
  if (!firstLine) return []
  return firstLine.split(',').map((h) => h.trim())
}

function parseMultiPreview(
  text: string,
  matches: ColumnMatchInfo[],
): { preview: MultiParsedRow[]; totalRows: number } {
  const lines = text.split('\n').filter((l) => l.trim())
  if (lines.length < 2) return { preview: [], totalRows: 0 }
  const headers = lines[0].split(',').map((h) => h.trim())
  const colIndexMap: Record<string, number> = {}
  for (let i = 0; i < headers.length; i++) colIndexMap[headers[i]] = i

  const numIdx = headers.findIndex((h) => ['numero_estudante', 'numero', 'id'].includes(normalize(h)))
  const nameIdx = headers.findIndex((h) => ['nome', 'aluno'].includes(normalize(h)))

  const dataLines = lines.slice(1)
  const allRows: MultiParsedRow[] = dataLines.map((line) => {
    const parts = line.split(',').map((p) => p.trim())
    const values: Record<string, string> = {}
    let validCount = 0
    for (const m of matches) {
      const idx = colIndexMap[m.csvColumn]
      const val = idx !== undefined ? (parts[idx] ?? '') : ''
      values[m.csvColumn] = val
      const n = parseFloat(val.replace(',', '.'))
      if (val && !isNaN(n) && n >= 0 && n <= 20) validCount++
    }
    return {
      numero: numIdx >= 0 ? (parts[numIdx] ?? '') : '',
      nome: nameIdx >= 0 ? (parts[nameIdx] ?? '') : '',
      values,
      validCount,
      totalMatched: matches.length,
    }
  })
  return { preview: allRows.slice(0, 3), totalRows: dataLines.length }
}

export function ImportCSVModal({ isOpen, onClose, components, onImport, onImportMulti }: ImportCSVModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null)

  const [mode, setMode] = useState<'single' | 'multi'>('single')
  const [selectedComponent, setSelectedComponent] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [csvText, setCsvText] = useState('')

  // Single mode
  const [preview, setPreview] = useState<ParsedRow[]>([])
  const [totalValid, setTotalValid] = useState(0)
  const [totalRows, setTotalRows] = useState(0)

  // Multi mode
  const [matchedColumns, setMatchedColumns] = useState<ColumnMatchInfo[]>([])
  const [multiPreview, setMultiPreview] = useState<MultiParsedRow[]>([])
  const [multiTotalRows, setMultiTotalRows] = useState(0)
  const [unmatchedHeaders, setUnmatchedHeaders] = useState<string[]>([])

  const [importing, setImporting] = useState(false)
  const [result, setResult] = useState<ImportResult | null>(null)
  const [multiResult, setMultiResult] = useState<MultiImportResult | null>(null)
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

  const handleFileSelect = useCallback((file: File) => {
    setSelectedFile(file)
    setResult(null)
    setMultiResult(null)
    setError(null)
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      setCsvText(text)

      const headers = parseCSVHeaders(text)
      const matches = detectMultiColumns(headers, components)

      if (matches.length > 0 && onImportMulti) {
        setMode('multi')
        setMatchedColumns(matches)
        const matchedSet = new Set(matches.map((m) => m.csvColumn))
        const nonGrade = new Set(headers.filter((h) => NON_GRADE_HEADERS.has(normalize(h))))
        setUnmatchedHeaders(headers.filter((h) => !matchedSet.has(h) && !nonGrade.has(h)))
        const mp = parseMultiPreview(text, matches)
        setMultiPreview(mp.preview)
        setMultiTotalRows(mp.totalRows)
      } else {
        setMode('single')
        setMatchedColumns([])
        const parsed = parseCSVPreview(text)
        setPreview(parsed.preview)
        setTotalValid(parsed.totalValid)
        setTotalRows(parsed.totalRows)
      }
    }
    reader.readAsText(file)
  }, [components, onImportMulti])

  const handleImport = async () => {
    if (!selectedFile) return

    if (mode === 'multi' && onImportMulti) {
      setImporting(true)
      setError(null)
      try {
        const res = await onImportMulti(selectedFile)
        setMultiResult(res)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erro ao importar')
      } finally {
        setImporting(false)
      }
    } else {
      if (!selectedComponent) return
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
  }

  const handleClose = () => {
    setMode('single')
    setSelectedComponent('')
    setSelectedFile(null)
    setCsvText('')
    setPreview([])
    setTotalValid(0)
    setTotalRows(0)
    setMatchedColumns([])
    setMultiPreview([])
    setMultiTotalRows(0)
    setUnmatchedHeaders([])
    setResult(null)
    setMultiResult(null)
    setError(null)
    onClose()
  }

  const switchToSingle = () => {
    setMode('single')
    setMatchedColumns([])
    if (csvText) {
      const parsed = parseCSVPreview(csvText)
      setPreview(parsed.preview)
      setTotalValid(parsed.totalValid)
      setTotalRows(parsed.totalRows)
    }
  }

  if (!isOpen) return null

  const canImport = mode === 'multi'
    ? !!selectedFile && matchedColumns.length > 0
    : !!selectedComponent && !!selectedFile

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
          <FileDropzone
            onFileSelect={handleFileSelect}
            accept=".csv"
            label={selectedFile ? `Ficheiro: ${selectedFile.name}` : 'Arraste o CSV aqui ou clique para seleccionar'}
          />

          {/* Multi-component detected banner */}
          {mode === 'multi' && matchedColumns.length > 0 && (
            <div className="rounded-lg bg-primary/10 border border-primary/20 px-4 py-3">
              <div className="flex items-center gap-2 mb-2">
                <Layers className="size-4 text-primary" />
                <span className="text-sm font-semibold text-foreground">
                  {matchedColumns.length} componente{matchedColumns.length > 1 ? 's' : ''} detectada{matchedColumns.length > 1 ? 's' : ''} no CSV
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {matchedColumns.map((m) => (
                  <span
                    key={m.csvColumn}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-success/10 border border-success/20 text-xs font-medium text-success"
                  >
                    <CheckCircle className="size-3" />
                    {m.csvColumn} &rarr; {m.componentName}
                  </span>
                ))}
              </div>
              {unmatchedHeaders.length > 0 && (
                <p className="text-xs text-muted-foreground">
                  Colunas ignoradas: {unmatchedHeaders.join(', ')}
                </p>
              )}
              <button
                type="button"
                onClick={switchToSingle}
                className="mt-2 text-xs text-primary hover:underline"
              >
                Importar apenas uma componente
              </button>
            </div>
          )}

          {/* Single mode: component selector */}
          {mode === 'single' && (
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
          )}

          {/* Multi mode preview */}
          {mode === 'multi' && multiPreview.length > 0 && (
            <div>
              <p className="text-sm font-medium text-foreground mb-2">
                Pré-visualização (primeiras {multiPreview.length} linhas):
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs border border-border rounded-md overflow-hidden">
                  <thead>
                    <tr className="bg-muted border-b border-border">
                      <th scope="col" className="text-left px-3 py-1.5 font-medium text-muted-foreground">Nº</th>
                      <th scope="col" className="text-left px-3 py-1.5 font-medium text-muted-foreground">Nome</th>
                      {matchedColumns.map((m) => (
                        <th key={m.csvColumn} scope="col" className="text-right px-3 py-1.5 font-medium text-muted-foreground">
                          {m.componentName}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {multiPreview.map((row, i) => (
                      <tr key={i}>
                        <td className="px-3 py-1 border-b border-border">{row.numero || '—'}</td>
                        <td className="px-3 py-1 border-b border-border">{row.nome || '—'}</td>
                        {matchedColumns.map((m) => {
                          const val = row.values[m.csvColumn] ?? ''
                          const n = parseFloat(val.replace(',', '.'))
                          const isValid = val !== '' && !isNaN(n) && n >= 0 && n <= 20
                          return (
                            <td
                              key={m.csvColumn}
                              className={`px-3 py-1 border-b border-border text-right ${!isValid && val ? 'text-destructive' : ''}`}
                            >
                              {val || '—'}
                            </td>
                          )
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div role="status" aria-live="polite" className="mt-2 text-xs text-muted-foreground">
                {multiTotalRows} aluno{multiTotalRows !== 1 ? 's' : ''} no ficheiro
              </div>
            </div>
          )}

          {/* Single mode preview */}
          {mode === 'single' && preview.length > 0 && (
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

          {/* Single mode result */}
          {result && (
            <div role="status" aria-live="polite" className="rounded-lg bg-success/10 border border-success/20 px-3 py-2 text-sm text-success flex items-center gap-2">
              <CheckCircle className="size-4 shrink-0" />
              {result.imported} notas importadas
              {result.unmatched > 0 && ` | ${result.unmatched} sem correspondência`}
            </div>
          )}

          {/* Multi mode result */}
          {multiResult && (
            <div role="status" aria-live="polite" className="rounded-lg bg-success/10 border border-success/20 px-3 py-2 text-sm text-success">
              <div className="flex items-center gap-2 mb-1">
                <CheckCircle className="size-4 shrink-0" />
                <span className="font-medium">{multiResult.total} notas importadas no total</span>
              </div>
              <ul className="ml-6 space-y-0.5">
                {multiResult.components.map((c) => (
                  <li key={c.csv_column} className="text-xs">
                    {c.component_name}: {c.count} nota{c.count !== 1 ? 's' : ''}
                  </li>
                ))}
              </ul>
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
            disabled={!canImport || importing}
          >
            {importing
              ? 'A importar…'
              : mode === 'multi'
                ? `Importar ${matchedColumns.length} componente${matchedColumns.length > 1 ? 's' : ''}`
                : 'Importar'
            }
          </Button>
        </div>
      </div>
    </div>
  )
}
