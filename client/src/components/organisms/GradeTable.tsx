import { useState, useRef, useEffect } from 'react'
import { Check, X } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { ContextItem, StudentRow } from '@/types'
import { calcNotaFinal, getRowBadgeLabel, BADGE_CLASSES } from '@/lib/grades'

type CellStatus = 'default' | 'saving' | 'error'

interface EditingCell {
  studentId: string
  componentId: string
  inputValue: string
}

interface GradeTableProps {
  contextItem: ContextItem
  rows: StudentRow[]
  onRowsChange: (updater: (prev: StudentRow[]) => StudentRow[]) => void
  onGradeUpdate: (gradeId: string, componentId: string, value: number) => Promise<void>
  filterText: string
  filterStatus: string
  sortBy: string
}

export function GradeTable({
  contextItem,
  rows,
  onRowsChange,
  onGradeUpdate,
  filterText,
  filterStatus,
  sortBy,
}: GradeTableProps) {
  const [editingCell, setEditingCell] = useState<EditingCell | null>(null)
  const [cellStatus, setCellStatus] = useState<Record<string, CellStatus>>({})
  const [cellError, setCellError] = useState<Record<string, string>>({})
  const inputRef = useRef<HTMLInputElement>(null)

  // Focus input when editing starts
  useEffect(() => {
    if (editingCell) {
      inputRef.current?.focus()
    }
  }, [editingCell])

  const cellKey = (studentId: string, componentId: string) => `${studentId}:${componentId}`

  const filteredRows = rows
    .filter((row) => {
      const matchText =
        filterText === '' ||
        row.studentName.toLowerCase().includes(filterText.toLowerCase()) ||
        row.studentNumber.includes(filterText)
      const badge = getRowBadgeLabel(row.components, contextItem.components, row.published)
      const matchStatus =
        filterStatus === 'todos' || badge.toLowerCase() === filterStatus.toLowerCase()
      return matchText && matchStatus
    })
    .sort((a, b) => {
      if (sortBy === 'nome') return a.studentName.localeCompare(b.studentName)
      if (sortBy === 'nota') {
        const na = calcNotaFinal(a.components, contextItem.components) ?? -1
        const nb = calcNotaFinal(b.components, contextItem.components) ?? -1
        return nb - na
      }
      return a.studentNumber.localeCompare(b.studentNumber)
    })

  const startEdit = (studentId: string, componentId: string, currentValue: number | null) => {
    const row = rows.find((r) => r.studentId === studentId)
    if (!row || row.published) return
    setEditingCell({
      studentId,
      componentId,
      inputValue: currentValue !== null && currentValue !== undefined ? String(currentValue) : '',
    })
  }

  const cancelEdit = () => setEditingCell(null)

  const confirmEdit = async () => {
    if (!editingCell) return
    const { studentId, componentId, inputValue } = editingCell
    const row = rows.find((r) => r.studentId === studentId)
    if (!row) return
    const gradeEntry = row.components[componentId]
    if (!gradeEntry) return

    const newValue = parseFloat(inputValue)
    const key = cellKey(studentId, componentId)

    if (isNaN(newValue) || newValue < 0 || newValue > 20) {
      setCellError((prev) => ({ ...prev, [key]: 'Valor inválido (0–20)' }))
      return
    }

    setEditingCell(null)
    setCellStatus((prev) => ({ ...prev, [key]: 'saving' }))
    setCellError((prev) => {
      const next = { ...prev }
      delete next[key]
      return next
    })

    try {
      await onGradeUpdate(gradeEntry.gradeId, componentId, newValue)
      onRowsChange((prev) =>
        prev.map((r) => {
          if (r.studentId !== studentId) return r
          return {
            ...r,
            components: {
              ...r.components,
              [componentId]: { ...r.components[componentId], value: newValue },
            },
          }
        }),
      )
      setCellStatus((prev) => {
        const next = { ...prev }
        delete next[key]
        return next
      })
    } catch (err) {
      setCellStatus((prev) => ({ ...prev, [key]: 'error' }))
      setCellError((prev) => ({
        ...prev,
        [key]: err instanceof Error ? err.message : 'Erro ao guardar',
      }))
    }
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <Table aria-label={`Notas da turma ${contextItem.turma}`}>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead scope="col" className="w-28 font-semibold text-foreground">
              Nº
            </TableHead>
            <TableHead scope="col" className="font-semibold text-foreground">
              Nome
            </TableHead>
            {contextItem.components.map((comp) => (
              <TableHead
                key={comp.id}
                scope="col"
                className="font-semibold text-foreground text-center min-w-[110px]"
              >
                {comp.name}
                <br />
                <span className="text-xs font-normal text-muted-foreground">({comp.weight}%)</span>
              </TableHead>
            ))}
            <TableHead scope="col" className="font-semibold text-foreground text-center w-28">
              Nota Final
            </TableHead>
            <TableHead scope="col" className="font-semibold text-foreground text-center w-28">
              Estado
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filteredRows.map((row) => {
            const notaFinal = calcNotaFinal(row.components, contextItem.components)
            const badgeLabel = getRowBadgeLabel(row.components, contextItem.components, row.published)
            const badgeCls = BADGE_CLASSES[badgeLabel] ?? ''

            return (
              <TableRow
                key={row.studentId}
                className={row.published ? 'opacity-70 bg-muted/50' : 'hover:bg-muted/50/50'}
              >
                {/* Student number as row header */}
                <TableHead
                  scope="row"
                  className="font-mono text-sm font-normal text-muted-foreground px-4 py-3"
                >
                  {row.studentNumber}
                </TableHead>
                <TableCell className="font-medium text-foreground">{row.studentName}</TableCell>

                {contextItem.components.map((comp) => {
                  const key = cellKey(row.studentId, comp.id)
                  const status = cellStatus[key] ?? 'default'
                  const error = cellError[key]
                  const gradeVal = row.components[comp.id]?.value
                  const isCellEditing =
                    editingCell?.studentId === row.studentId &&
                    editingCell?.componentId === comp.id

                  let cellBg = ''
                  if (isCellEditing) cellBg = 'bg-[#EFF6FF]'
                  else if (status === 'saving') cellBg = 'bg-muted'
                  else if (status === 'error') cellBg = 'bg-[#FEF2F2]'

                  return (
                    <TableCell
                      key={comp.id}
                      className={[
                        'text-center py-2',
                        cellBg,
                        status === 'error' ? 'ring-1 ring-inset ring-destructive' : '',
                        !row.published && !isCellEditing ? 'cursor-pointer' : '',
                      ]
                        .filter(Boolean)
                        .join(' ')}
                      onDoubleClick={() =>
                        !row.published && startEdit(row.studentId, comp.id, gradeVal ?? null)
                      }
                    >
                      {isCellEditing ? (
                        <div className="flex items-center gap-1 justify-center">
                          <input
                            ref={inputRef}
                            type="number"
                            min="0"
                            max="20"
                            step="0.1"
                            value={editingCell.inputValue}
                            onChange={(e) =>
                              setEditingCell((prev) =>
                                prev ? { ...prev, inputValue: e.target.value } : null,
                              )
                            }
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') confirmEdit()
                              if (e.key === 'Escape') cancelEdit()
                            }}
                            aria-label={`Nota de ${comp.name} para ${row.studentName}`}
                            className="w-16 text-center border border-primary rounded px-1 py-0.5 text-sm focus:outline-none focus:ring-1 focus:ring-primary"
                          />
                          <button
                            type="button"
                            onClick={confirmEdit}
                            aria-label="Guardar nota"
                            className="text-success hover:text-success/80 text-base leading-none"
                          >
                            <Check className="size-4" />
                          </button>
                          <button
                            type="button"
                            onClick={cancelEdit}
                            aria-label="Cancelar edição"
                            className="text-muted-foreground hover:text-foreground text-sm leading-none"
                          >
                            <X className="size-3.5" />
                          </button>
                        </div>
                      ) : status === 'saving' ? (
                        <span className="text-muted-foreground text-xs animate-pulse">A guardar…</span>
                      ) : (
                        <div className="flex flex-col items-center gap-0.5">
                          <span
                            className={
                              gradeVal !== null && gradeVal !== undefined
                                ? 'text-foreground tabular-nums'
                                : 'text-muted-foreground/30 text-xs'
                            }
                          >
                            {gradeVal !== null && gradeVal !== undefined ? gradeVal : '—'}
                          </span>
                          {error && (
                            <span className="text-[#B91C1C] text-xs">{error}</span>
                          )}
                        </div>
                      )}
                    </TableCell>
                  )
                })}

                <TableCell className="text-center font-semibold tabular-nums">
                  {notaFinal !== null ? (
                    <span className={notaFinal >= 10 ? 'text-[#15803D]' : 'text-[#B91C1C]'}>
                      {notaFinal.toFixed(1)}
                    </span>
                  ) : (
                    <span className="text-muted-foreground/30 text-xs">—</span>
                  )}
                </TableCell>

                <TableCell className="text-center">
                  <span
                    className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${badgeCls}`}
                  >
                    {badgeLabel}
                  </span>
                </TableCell>
              </TableRow>
            )
          })}

          {filteredRows.length === 0 && (
            <TableRow>
              <TableCell
                colSpan={contextItem.components.length + 4}
                className="text-center text-muted-foreground py-10"
              >
                Nenhum estudante corresponde aos filtros seleccionados.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
    </div>
  )
}
