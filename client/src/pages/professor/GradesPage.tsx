import { useState, useMemo, useCallback, useRef, useEffect } from 'react'
import { Download, BarChart2, TrendingUp, TrendingDown, CheckCircle, XCircle, Clock } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { AppHeader } from '@/components/organisms/AppHeader'
import { SearchBar } from '@/components/molecules/SearchBar'
import { useActiveContext } from '@/contexts/ActiveContextContext'
import { StatCard } from '@/components/molecules/StatCard'
import { GradeTable } from '@/components/organisms/GradeTable'
import { ImportCSVModal } from '@/components/organisms/ImportCSVModal'
import { apiFetch } from '@/lib/api'
import { calcNotaFinal, getRowBadgeLabel } from '@/lib/grades'
import type { ContextItem, StudentRow, ImportHistoryEntry } from '@/types'


// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function formatTimestamp(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('pt-PT', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------
export default function GradesPage() {
  const navigate = useNavigate()
  const { activeContextId } = useActiveContext()

  const [contextItem, setContextItem] = useState<ContextItem | null>(null)
  const [rows, setRows] = useState<StudentRow[]>([])
  const [loading, setLoading] = useState(true)
  const [importHistory, setImportHistory] = useState<ImportHistoryEntry[]>([])
  const [historyExpanded, setHistoryExpanded] = useState(false)

  // UI
  const [filterText, setFilterText] = useState('')
  const [filterStatus, setFilterStatus] = useState('todos')
  const [sortBy, setSortBy] = useState('numero')
  const [importModalOpen, setImportModalOpen] = useState(false)
  const [statusMsg, setStatusMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null)
  const statusTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showStatus = useCallback((text: string, type: 'success' | 'error') => {
    setStatusMsg({ text, type })
    if (statusTimerRef.current) clearTimeout(statusTimerRef.current)
    statusTimerRef.current = setTimeout(() => setStatusMsg(null), 4000)
  }, [])

  const loadData = useCallback(async (contextId: string) => {
    setLoading(true)
    try {
      const ctx = await apiFetch<ContextItem>(`/academic-contexts/${contextId}`)
      setContextItem(ctx)
      const gradesData = await apiFetch<{ students: StudentRow[] }>(`/grades/?context_id=${contextId}`)
      setRows(gradesData.students ?? [])
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Erro ao carregar notas'
      showStatus(msg, 'error')
      setContextItem(null)
      setRows([])
    } finally {
      setLoading(false)
    }
  }, [showStatus])

  useEffect(() => {
    if (activeContextId) {
      void loadData(activeContextId)
    } else {
      setLoading(false)
    }
  }, [activeContextId, loadData])

  // Derived stats
  const stats = useMemo(() => {
    if (!contextItem) return { media: '—', alta: '—', baixa: '—', aprovados: '0 (0%)', reprovados: '0 (0%)', incompletos: '0 (0%)' }
    const allComputed = rows.map((r) => ({
      nota: calcNotaFinal(r.components, contextItem.components),
      published: r.published,
      badge: getRowBadgeLabel(r.components, contextItem.components, r.published),
    }))
    const notas = allComputed
      .filter((r) => r.nota !== null && (r.badge === 'Lançada' || r.published))
      .map((r) => r.nota as number)

    const media = notas.length ? notas.reduce((s, n) => s + n, 0) / notas.length : null
    const alta = notas.length ? Math.max(...notas) : null
    const baixa = notas.length ? Math.min(...notas) : null
    const aprovados = notas.filter((n) => n >= 10).length
    const reprovados = notas.filter((n) => n < 10).length
    const incompletos = allComputed.filter((r) => r.badge === 'Incompleta' || r.badge === 'Vazio').length
    const pct = (n: number) => rows.length > 0 ? `${n} (${Math.round((n / rows.length) * 100)}%)` : `${n} (0%)`

    return {
      media: media !== null ? media.toFixed(1) : '—',
      alta: alta !== null ? String(alta) : '—',
      baixa: baixa !== null ? String(baixa) : '—',
      aprovados: pct(aprovados),
      reprovados: pct(reprovados),
      incompletos: pct(incompletos),
    }
  }, [rows, contextItem])

  const incompleteCount = useMemo(
    () => !contextItem ? 0 : rows.filter((r) => {
      const b = getRowBadgeLabel(r.components, contextItem.components, r.published)
      return b === 'Incompleta' || b === 'Vazio'
    }).length,
    [rows, contextItem],
  )

  // Handlers
  const handleGradeUpdate = useCallback(async (gradeId: string, _componentId: string, value: number) => {
    await apiFetch(`/grades/${gradeId}`, {
      method: 'PATCH',
      body: JSON.stringify({ value }),
    })
    // Errors propagate to GradeTable.confirmEdit's catch → sets cellStatus 'error'
  }, [])

  const handleImport = useCallback(
    async (componentId: string, file: File): Promise<{ imported: number; unmatched: number }> => {
      if (!contextItem) return { imported: 0, unmatched: 0 }
      const compName = contextItem.components.find((c) => c.id === componentId)?.name ?? componentId
      try {
        const formData = new FormData()
        formData.append('file', file)
        const res = await apiFetch<{ count: number; grades: unknown[] }>(`/api/v1/grades/upload?context_id=${contextItem.id}`, {
          method: 'POST',
          body: formData,
          headers: {},
        })
        const entry: ImportHistoryEntry = {
          id: crypto.randomUUID(),
          componentName: compName,
          timestamp: new Date().toISOString(),
          count: res.count,
        }
        setImportHistory((prev) => [entry, ...prev].slice(0, 10))
        showStatus(`${res.count} notas importadas para ${compName}`, 'success')
        if (activeContextId) void loadData(activeContextId)
        return { imported: res.count, unmatched: 0 }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Erro ao importar notas'
        showStatus(`Erro: ${errorMsg}`, 'error')
        throw err
      }
    },
    [contextItem, activeContextId, loadData, showStatus],
  )

  if (loading || !contextItem) {
    return (
      <div className="min-h-screen bg-background">
        <AppHeader activeTab="notas" />
        <main className="max-w-[1280px] mx-auto px-6 py-16 flex items-center justify-center">
          <span className="text-muted-foreground animate-pulse">
            {loading ? 'A carregar notas…' : 'Selecione um contexto académico no topo da página.'}
          </span>
        </main>
      </div>
    )
  }

  const breadcrumb = `${contextItem.turma} · ${contextItem.disciplina} · ${contextItem.semestre} · ${contextItem.turno}`
  const visibleHistory = historyExpanded ? importHistory : importHistory.slice(0, 3)

  return (
    <div className="min-h-screen bg-background">
      <AppHeader activeTab="notas" />

      <main className="max-w-[1280px] mx-auto px-6 py-6 flex flex-col gap-5">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">Notas</span>
          <span className="text-muted-foreground">/</span>
          <span className="text-muted-foreground truncate">{breadcrumb}</span>
        </div>

        {/* Title + toolbar */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-xl font-bold text-foreground">Gestão de Notas</h1>
            <p className="text-sm text-muted-foreground mt-0.5">{breadcrumb}</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setImportModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              <Download className="size-4" /> Importar CSV
            </button>

            <button
              type="button"
              onClick={() => { void loadData(activeContextId!); showStatus('Notas actualizadas da base de dados.', 'success') }}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-border bg-card text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              🧮 Recalcular
            </button>

            <button
              type="button"
              onClick={() => navigate(`/publicar?context=${contextItem.id}`)}
              title={incompleteCount > 0 ? `${incompleteCount} notas incompletas — serão excluídas da publicação` : undefined}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-md bg-primary text-white text-sm font-medium hover:bg-primary/90 transition-colors"
            >
              📤 Publicar notas
              {incompleteCount > 0 && (
                <span className="ml-1 bg-card/20 text-xs px-1.5 py-0.5 rounded-full">
                  {incompleteCount}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Status message */}
        {statusMsg && (
          <div
            role="status"
            aria-live="polite"
            className={[
              'rounded-md px-4 py-2.5 text-sm font-medium',
              statusMsg.type === 'success'
                ? 'bg-success/10 border border-success/20 text-success'
                : 'bg-destructive/10 border border-destructive/20 text-destructive',
            ].join(' ')}
          >
            {statusMsg.text}
          </div>
        )}

        {/* Filter bar */}
        <div className="flex flex-wrap gap-3 items-center">
          <div className="flex-1 min-w-[200px] max-w-xs">
            <SearchBar
              value={filterText}
              onChange={setFilterText}
              placeholder="Pesquisar por nome ou nº…"
            />
          </div>

          <div className="flex items-center gap-1.5">
            <label htmlFor="filter-status" className="text-sm text-muted-foreground whitespace-nowrap">
              Mostrar:
            </label>
            <select
              id="filter-status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="border border-border rounded-md px-3 py-1.5 text-sm bg-card focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="todos">Todos</option>
              <option value="lançada">Completos</option>
              <option value="incompleta">Incompletos</option>
              <option value="vazio">Vazios</option>
              <option value="publicada">Publicados</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <label htmlFor="sort-by" className="text-sm text-muted-foreground whitespace-nowrap">
              Ordenar:
            </label>
            <select
              id="sort-by"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="border border-border rounded-md px-3 py-1.5 text-sm bg-card focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="numero">Número</option>
              <option value="nome">Nome</option>
              <option value="nota">Nota Final</option>
            </select>
          </div>
        </div>

        {/* Table */}
        <GradeTable
          contextItem={contextItem}
          rows={rows}
          onRowsChange={setRows}
          onGradeUpdate={handleGradeUpdate}
          filterText={filterText}
          filterStatus={filterStatus}
          sortBy={sortBy}
        />

        {/* Stats */}
        <section aria-label="Estatísticas da turma">
          <h2 className="text-sm font-semibold text-foreground mb-3">Estatísticas da turma</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <StatCard icon={<BarChart2 className="size-4" />} label="Nota média" value={stats.media} />
            <StatCard icon={<TrendingUp className="size-4" />} label="Nota mais alta" variant="success" value={stats.alta} />
            <StatCard icon={<TrendingDown className="size-4" />} label="Nota mais baixa" variant="danger" value={stats.baixa} />
            <StatCard icon={<CheckCircle className="size-4" />} label="Aprovados" variant="success" value={stats.aprovados} />
            <StatCard icon={<XCircle className="size-4" />} label="Reprovados" variant="danger" value={stats.reprovados} />
            <StatCard icon={<Clock className="size-4" />} label="Incompletos" variant="warning" value={stats.incompletos} />
          </div>
        </section>

        {/* Import history */}
        {importHistory.length > 0 && (
          <section aria-label="Histórico de importações">
            <h2 className="text-sm font-semibold text-foreground mb-3">Histórico de importações</h2>
            <div className="bg-card rounded-lg border border-border divide-y divide-border">
              {visibleHistory.map((entry) => (
                <div key={entry.id} className="px-4 py-3 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-3">
                    <span className="text-muted-foreground font-mono text-xs">
                      {formatTimestamp(entry.timestamp)}
                    </span>
                    <span className="text-foreground font-medium">{entry.componentName}</span>
                  </div>
                  <span className="text-success font-medium">{entry.count} notas</span>
                </div>
              ))}
              {importHistory.length > 3 && (
                <div className="px-4 py-2.5">
                  <button
                    type="button"
                    onClick={() => setHistoryExpanded((p) => !p)}
                    className="text-sm text-primary hover:underline"
                  >
                    {historyExpanded
                      ? 'Ver menos'
                      : `Ver log completo (${importHistory.length} entradas)`}
                  </button>
                </div>
              )}
            </div>
          </section>
        )}
      </main>

      <ImportCSVModal
        isOpen={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        components={contextItem.components}
        onImport={handleImport}
      />
    </div>
  )
}
