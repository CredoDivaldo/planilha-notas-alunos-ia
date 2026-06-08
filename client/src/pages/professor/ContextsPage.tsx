import { useState, useMemo, useEffect, useRef } from 'react'
import { AppHeader } from '@/components/organisms/AppHeader'
import { SearchBar } from '@/components/molecules/SearchBar'
import { FileDropzone } from '@/components/molecules/FileDropzone'
import { ContextModal } from '@/components/organisms/ContextModal'
import type { ContextPayload } from '@/components/organisms/ContextModal'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { apiFetch } from '@/lib/api'
import type { ContextItem } from '@/types'

const FALLBACK_CONTEXTS: ContextItem[] = [
  {
    id: '1',
    turma: 'ING-T1',
    disciplina: 'Inglês Técnico',
    semestre: '2026/1',
    turno: 'Manhã',
    alunosCount: 42,
    delegado: { id: 'a1', name: 'Carlos Mendes', studentNumber: '22009' },
    components: [
      { id: 'c1', name: 'Frequência', weight: 40 },
      { id: 'c2', name: 'Exame Final', weight: 60 },
    ],
  },
  {
    id: '2',
    turma: 'ING-T2',
    disciplina: 'Inglês Técnico',
    semestre: '2026/1',
    turno: 'Tarde',
    alunosCount: 38,
    delegado: null,
    components: [
      { id: 'c3', name: 'Teste 1', weight: 30 },
      { id: 'c4', name: 'Teste 2', weight: 30 },
      { id: 'c5', name: 'Exame', weight: 40 },
    ],
  },
  {
    id: '3',
    turma: 'MAT-T1',
    disciplina: 'Matemática',
    semestre: '2026/1',
    turno: 'Manhã',
    alunosCount: 40,
    delegado: null,
    components: [],
  },
  {
    id: '4',
    turma: 'FIS-T1',
    disciplina: 'Física',
    semestre: '2025/2',
    turno: 'Manhã',
    alunosCount: 35,
    delegado: null,
    components: [],
  },
  {
    id: '5',
    turma: 'QUI-T1',
    disciplina: 'Química',
    semestre: '2025/2',
    turno: 'Tarde',
    alunosCount: 37,
    delegado: null,
    components: [],
  },
]

type StatusMsg = { type: 'success' | 'error'; text: string }

export default function ContextsPage() {
  const [contexts, setContexts] = useState<ContextItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [filterSemestre, setFilterSemestre] = useState('todos')
  const [filterTurno, setFilterTurno] = useState('todos')

  const [modalOpen, setModalOpen] = useState(false)
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
  const [editTarget, setEditTarget] = useState<ContextItem | null>(null)

  const [deleteTarget, setDeleteTarget] = useState<ContextItem | null>(null)
  const [deleting, setDeleting] = useState(false)

  const [csvUploading, setCsvUploading] = useState(false)
  const [csvError, setCsvError] = useState<string | undefined>()

  const [statusMsg, setStatusMsg] = useState<StatusMsg | null>(null)
  const statusTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showStatus = (msg: StatusMsg) => {
    setStatusMsg(msg)
    if (statusTimer.current) clearTimeout(statusTimer.current)
    statusTimer.current = setTimeout(() => setStatusMsg(null), 4000)
  }

  useEffect(() => {
    apiFetch<ContextItem[]>('/academic-contexts/')
      .then(setContexts)
      .catch(() => setContexts(FALLBACK_CONTEXTS))
      .finally(() => setLoading(false))
  }, [])

  const selectedContext = useMemo(
    () => contexts.find((c) => c.id === selectedId) ?? null,
    [contexts, selectedId],
  )

  const semestres = useMemo(() => {
    return Array.from(new Set(contexts.map((c) => c.semestre))).sort().reverse()
  }, [contexts])

  const turnos = useMemo(() => {
    return Array.from(new Set(contexts.map((c) => c.turno))).sort()
  }, [contexts])

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return contexts.filter((c) => {
      const matchesSearch = !q || c.turma.toLowerCase().includes(q) || c.disciplina.toLowerCase().includes(q)
      const matchesSemestre = filterSemestre === 'todos' || c.semestre === filterSemestre
      const matchesTurno = filterTurno === 'todos' || c.turno === filterTurno
      return matchesSearch && matchesSemestre && matchesTurno
    })
  }, [contexts, search, filterSemestre, filterTurno])

  const handleCreateOpen = () => {
    setModalMode('create')
    setEditTarget(null)
    setModalOpen(true)
  }

  const handleEditOpen = (ctx: ContextItem) => {
    setModalMode('edit')
    setEditTarget(ctx)
    setModalOpen(true)
  }

  const handleModalSubmit = async (payload: ContextPayload): Promise<void> => {
    if (modalMode === 'create') {
      try {
        const created = await apiFetch<ContextItem>('/academic-contexts/', {
          method: 'POST',
          body: JSON.stringify(payload),
        })
        setContexts((prev) => [...prev, created])
      } catch {
        const mockItem: ContextItem = {
          id: crypto.randomUUID(),
          turma: payload.turma,
          disciplina: payload.disciplina,
          semestre: payload.semestre,
          turno: payload.turno,
          alunosCount: 0,
          delegado: null,
          components: payload.components.map((c, i) => ({
            id: String(i),
            name: c.name,
            weight: c.weight,
          })),
        }
        setContexts((prev) => [...prev, mockItem])
      }
      setModalOpen(false)
      showStatus({ type: 'success', text: 'Contexto criado com sucesso.' })
    } else if (editTarget) {
      const updated = await apiFetch<ContextItem>(`/academic-contexts/${editTarget.id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      })
      setContexts((prev) => prev.map((c) => (c.id === editTarget.id ? updated : c)))
      setModalOpen(false)
      showStatus({ type: 'success', text: 'Contexto actualizado.' })
    }
  }

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await apiFetch(`/academic-contexts/${deleteTarget.id}`, { method: 'DELETE' })
    } catch {
      // no backend — remove locally
    }
    setContexts((prev) => prev.filter((c) => c.id !== deleteTarget.id))
    if (selectedId === deleteTarget.id) setSelectedId(null)
    showStatus({ type: 'success', text: 'Contexto eliminado.' })
    setDeleting(false)
    setDeleteTarget(null)
  }

  const handleCsvUpload = async (file: File) => {
    if (!selectedContext) return
    setCsvUploading(true)
    setCsvError(undefined)
    try {
      const form = new FormData()
      form.append('file', file)
      const stored = localStorage.getItem('auth_user')
      const token: string | null = stored
        ? (JSON.parse(stored) as { token: string }).token
        : null
      const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
      const res = await fetch(
        `${base}/students/upload?context_id=${selectedContext.id}`,
        {
          method: 'POST',
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: form,
        },
      )
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText })) as { detail?: string }
        throw new Error(err.detail ?? `Upload falhou: ${res.status}`)
      }
      showStatus({ type: 'success', text: 'Estudantes importados com sucesso.' })
    } catch (err) {
      setCsvError(err instanceof Error ? err.message : 'Erro ao importar CSV.')
    } finally {
      setCsvUploading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <AppHeader activeTab="contextos" />

      <main className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-semibold text-slate-900">
            Gestão de Contextos Académicos
          </h1>
          <Button
            onClick={handleCreateOpen}
            className="bg-[#0D6EFD] hover:bg-[#0D6EFD]/90 text-white"
          >
            + Criar Contexto
          </Button>
        </div>

        {statusMsg && (
          <div
            role="status"
            aria-live="polite"
            className={[
              'mb-4 rounded px-4 py-2.5 text-sm border',
              statusMsg.type === 'success'
                ? 'bg-green-50 border-green-200 text-[#15803D]'
                : 'bg-red-50 border-red-200 text-[#B91C1C]',
            ].join(' ')}
          >
            {statusMsg.text}
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3 mb-4">
          <SearchBar
            value={search}
            onChange={setSearch}
            placeholder="Filtrar por turma, disciplina ou semestre"
          />
          <Select value={filterSemestre} onValueChange={setFilterSemestre}>
            <SelectTrigger className="w-36">
              <SelectValue placeholder="Semestre" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Semestre</SelectItem>
              {semestres.map((s) => (
                <SelectItem key={s} value={s}>{s}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={filterTurno} onValueChange={setFilterTurno}>
            <SelectTrigger className="w-32">
              <SelectValue placeholder="Turno" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="todos">Turno</SelectItem>
              {turnos.map((t) => (
                <SelectItem key={t} value={t}>{t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {loading ? (
          <div
            className="flex justify-center items-center py-16"
            aria-live="polite"
            aria-label="A carregar contextos"
          >
            <div className="w-8 h-8 border-4 border-[#0D6EFD] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <Table aria-label="Contextos Académicos">
              <TableHeader>
                <TableRow>
                  <TableHead scope="col">Turma</TableHead>
                  <TableHead scope="col">Disciplina</TableHead>
                  <TableHead scope="col">Semestre</TableHead>
                  <TableHead scope="col">Turno</TableHead>
                  <TableHead scope="col">Alunos</TableHead>
                  <TableHead scope="col" className="text-right">Acções</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-12 text-[#475569]">
                      Nenhum contexto encontrado.
                    </TableCell>
                  </TableRow>
                ) : (
                  filtered.map((ctx) => (
                    <TableRow
                      key={ctx.id}
                      data-state={selectedId === ctx.id ? 'selected' : undefined}
                      onClick={() => setSelectedId(selectedId === ctx.id ? null : ctx.id)}
                      className="cursor-pointer"
                      aria-selected={selectedId === ctx.id}
                    >
                      <TableCell className="font-medium">{ctx.turma}</TableCell>
                      <TableCell>{ctx.disciplina}</TableCell>
                      <TableCell>{ctx.semestre}</TableCell>
                      <TableCell>{ctx.turno}</TableCell>
                      <TableCell>{ctx.alunosCount}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <button
                            type="button"
                            aria-label={`Editar ${ctx.turma}`}
                            onClick={(e) => { e.stopPropagation(); handleEditOpen(ctx) }}
                            className="p-1.5 rounded hover:bg-slate-100 transition-colors"
                          >
                            ✏️
                          </button>
                          <button
                            type="button"
                            aria-label={`Eliminar ${ctx.turma}`}
                            onClick={(e) => { e.stopPropagation(); setDeleteTarget(ctx) }}
                            className="p-1.5 rounded hover:bg-red-50 transition-colors"
                          >
                            🗑
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        )}

        {selectedContext && (
          <div className="mt-4 bg-white rounded-lg border border-slate-200 shadow-sm p-6">
            <h2 className="text-base font-semibold text-slate-900 mb-4">
              Detalhe: {selectedContext.turma} · {selectedContext.disciplina} · {selectedContext.semestre}
            </h2>

            <section aria-labelledby="detail-components-heading">
              <h3
                id="detail-components-heading"
                className="text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wide"
              >
                Componentes de Avaliação
              </h3>
              <div className="bg-white border border-slate-200 rounded overflow-hidden mb-3">
                <table className="w-full text-sm" aria-label="Componentes de avaliação do contexto seleccionado">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50">
                      <th scope="col" className="text-left px-3 py-2 font-medium text-slate-600">Componente</th>
                      <th scope="col" className="text-left px-3 py-2 font-medium text-slate-600 w-24">Peso</th>
                      <th scope="col" className="w-10 px-3 py-2" aria-label="Acções" />
                    </tr>
                  </thead>
                  <tbody>
                    {selectedContext.components.length === 0 ? (
                      <tr>
                        <td colSpan={3} className="text-center px-3 py-4 text-[#475569] text-sm">
                          Sem componentes de avaliação definidos.
                        </td>
                      </tr>
                    ) : (
                      <>
                        {selectedContext.components.map((comp) => (
                          <tr key={comp.id} className="border-b border-slate-100">
                            <td className="px-3 py-2">{comp.name}</td>
                            <td className="px-3 py-2">{comp.weight}%</td>
                            <td className="px-3 py-2">
                              <button
                                type="button"
                                aria-label={`Editar componente ${comp.name}`}
                                onClick={() => handleEditOpen(selectedContext)}
                                className="hover:bg-slate-100 p-1 rounded transition-colors"
                              >
                                ✏️
                              </button>
                            </td>
                          </tr>
                        ))}
                        <tr className="bg-slate-50">
                          <td className="px-3 py-2 font-semibold text-slate-700">Total</td>
                          <td className="px-3 py-2 font-semibold text-[#15803D]">
                            {selectedContext.components.reduce((s, c) => s + c.weight, 0)}%
                          </td>
                          <td />
                        </tr>
                      </>
                    )}
                  </tbody>
                </table>
              </div>
              <button
                type="button"
                onClick={() => handleEditOpen(selectedContext)}
                className="text-sm text-[#0D6EFD] hover:underline"
              >
                + Adicionar componente
              </button>
            </section>

            <section aria-labelledby="detail-students-heading" className="mt-5">
              <h3
                id="detail-students-heading"
                className="text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wide"
              >
                Estudantes Associados
              </h3>
              <p className="text-sm text-[#475569] mb-3">
                <strong>{selectedContext.alunosCount}</strong> alunos
              </p>
              <div className="flex flex-wrap gap-2 mb-4">
                <Button
                  variant="outline"
                  size="sm"
                  className="text-[#0D6EFD] border-[#0D6EFD] hover:bg-[#0D6EFD]/5"
                >
                  👥 Ver estudantes
                </Button>
              </div>
              <FileDropzone
                onFileSelect={handleCsvUpload}
                isLoading={csvUploading}
                error={csvError}
                label="+ Importar via CSV — arraste ou clique para seleccionar"
              />
            </section>

            <section aria-labelledby="detail-delegate-heading" className="mt-5">
              <h3
                id="detail-delegate-heading"
                className="text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wide"
              >
                Delegado Atribuído
              </h3>
              {selectedContext.delegado ? (
                <div className="flex items-center gap-3">
                  <span className="text-sm text-slate-900">
                    {selectedContext.delegado.name} ({selectedContext.delegado.studentNumber})
                  </span>
                  <button type="button" className="text-sm text-[#0D6EFD] hover:underline">
                    Alterar delegado
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <span className="text-sm text-[#475569]">Sem delegado atribuído</span>
                  <button type="button" className="text-sm text-[#0D6EFD] hover:underline">
                    Atribuir delegado
                  </button>
                </div>
              )}
            </section>
          </div>
        )}
      </main>

      <ContextModal
        isOpen={modalOpen}
        mode={modalMode}
        initialData={editTarget}
        onClose={() => setModalOpen(false)}
        onSubmit={handleModalSubmit}
      />

      <Dialog open={!!deleteTarget} onOpenChange={(open) => { if (!open) setDeleteTarget(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmar eliminação</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-slate-700">
            Eliminar o contexto{' '}
            <strong>
              {deleteTarget?.turma} · {deleteTarget?.disciplina}
            </strong>
            ? Esta acção não pode ser revertida.
          </p>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteTarget(null)}
              disabled={deleting}
            >
              Cancelar
            </Button>
            <Button
              onClick={handleDeleteConfirm}
              disabled={deleting}
              className="bg-[#B91C1C] hover:bg-red-800 text-white"
            >
              {deleting ? 'A eliminar…' : 'Eliminar'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
