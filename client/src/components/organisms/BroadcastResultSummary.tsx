import { CheckCircle, AlertTriangle, ClipboardList, Smartphone, RotateCcw, Download, ArrowLeft } from 'lucide-react'
import { StatCard } from '@/components/molecules/StatCard'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

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
      <div className="text-center">
        <div className="flex justify-center mb-3">
          <CheckCircle className="size-12 text-success" />
        </div>
        <h2 className="text-xl font-bold text-foreground">Publicação Concluída</h2>
        <p className="text-sm text-muted-foreground mt-1">
          As notas foram publicadas no portal e as notificações foram enviadas.
        </p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <StatCard
          icon={<ClipboardList className="size-4" />}
          label="Publicadas no portal"
          value={result.portalPublished}
          variant="success"
        />
        <StatCard
          icon={<Smartphone className="size-4" />}
          label="WhatsApp enviados"
          value={result.whatsappSent}
          variant="success"
        />
        <StatCard
          icon={<AlertTriangle className="size-4" />}
          label="Falhas de envio"
          value={result.failures}
          variant={result.failures > 0 ? 'danger' : 'default'}
        />
      </div>

      {hasFailures && (
        <div className="bg-card rounded-lg border border-border overflow-hidden">
          <div className="px-4 py-3 border-b border-border flex items-center gap-2">
            <span className="text-sm font-semibold text-foreground">Falhas de Envio</span>
            <Badge variant="destructive">{result.failureList.length}</Badge>
          </div>
          <div className="divide-y divide-border">
            {result.failureList.map((f) => (
              <div key={f.studentId} className="px-4 py-3 flex items-center justify-between text-sm">
                <div>
                  <span className="font-medium text-foreground">{f.studentName}</span>
                  <span className="text-muted-foreground font-mono text-xs ml-2">({f.studentNumber})</span>
                </div>
                <Badge variant="destructive" className="text-xs">{f.reason}</Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="flex flex-wrap gap-3">
        <Button
          onClick={onResend}
          disabled={!hasFailures || resending}
          className="gap-2"
        >
          <RotateCcw className={`size-4 ${resending ? 'animate-spin' : ''}`} />
          {resending ? 'A reenviar…' : 'Re-enviar para falhados'}
        </Button>
        <Button variant="outline" onClick={onExport} className="gap-2">
          <Download className="size-4" /> Exportar relatório
        </Button>
        <Button variant="ghost" onClick={onBack} className="gap-2">
          <ArrowLeft className="size-4" /> Voltar ao painel
        </Button>
      </div>
    </div>
  )
}
