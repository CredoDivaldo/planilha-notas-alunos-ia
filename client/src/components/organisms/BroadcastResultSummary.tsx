// BroadcastResultSummary — O09 — Result screen after broadcast
// Shows 3 StatCards + failure list + 3 action buttons
// Rendered by PublishPage after POST /broadcast/ succeeds

import { StatCard } from '@/components/molecules/StatCard'

export interface BroadcastFailure {
  studentId: string
  studentName: string
  studentNumber: string
  reason: string
}

export interface BroadcastResult {
  portalPublished: number
  whatsappSent: number
  failures: number
  failureList: BroadcastFailure[]
}

interface BroadcastResultSummaryProps {
  result: BroadcastResult
  onResend: () => void
  onExport: () => void
  onBack: () => void
  resending?: boolean
}

export function BroadcastResultSummary({
  result,
  onResend,
  onExport,
  onBack,
  resending = false,
}: BroadcastResultSummaryProps) {
  const hasFailures = result.failureList.length > 0

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="text-center">
        <div className="text-3xl mb-2">✅</div>
        <h2 className="text-xl font-bold text-slate-900">PUBLICAÇÃO CONCLUÍDA</h2>
        <p className="text-sm text-slate-500 mt-1">
          As notas foram publicadas no portal e as notificações foram enviadas.
        </p>
      </div>

      {/* StatCards */}
      <div className="grid grid-cols-3 gap-4">
        <StatCard icon="📋" label="Publicadas no portal" value={result.portalPublished} />
        <StatCard icon="📱" label="WhatsApp enviados" value={result.whatsappSent} />
        <StatCard
          icon={result.failures > 0 ? '⚠️' : '✅'}
          label="Falhas de envio"
          value={result.failures}
        />
      </div>

      {/* Failure list */}
      {hasFailures && (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 flex items-center gap-2">
            <span className="text-sm font-semibold text-slate-700">Falhas de Envio</span>
            <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full font-medium">
              {result.failureList.length}
            </span>
          </div>
          <div className="divide-y divide-slate-100">
            {result.failureList.map((f) => (
              <div
                key={f.studentId}
                className="px-4 py-3 flex items-center justify-between text-sm"
              >
                <div>
                  <span className="font-medium text-slate-900">{f.studentName}</span>
                  <span className="text-slate-400 font-mono text-xs ml-2">({f.studentNumber})</span>
                </div>
                <span className="text-xs text-[#B91C1C] bg-red-50 px-2 py-0.5 rounded">
                  {f.reason}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={onResend}
          disabled={!hasFailures || resending}
          aria-disabled={!hasFailures || resending}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-[#0D6EFD] text-white text-sm font-medium hover:bg-[#0D6EFD]/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {resending ? (
            <>
              <span className="animate-spin text-xs">⏳</span>
              A reenviar…
            </>
          ) : (
            '🔄 Re-enviar para falhados'
          )}
        </button>

        <button
          type="button"
          onClick={onExport}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-slate-300 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
        >
          📥 Exportar relatório
        </button>

        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-slate-300 bg-white text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors"
        >
          ← Voltar ao painel
        </button>
      </div>
    </div>
  )
}
